def find_expression(key=None, array=[]):
    result = { 'level': -1, 'index': -1, 'value': None }
    if key is None: 
        return result

    n = -1
    count = -1
    for a in array:
        if '&' in a or '|' in a:
            n = -1
            count += 1
        if key in a:
            if count < 0: 
                count += 1
            result['level'] = count
            result['index'] = n+1
            result['value'] = a
            return result
        else: 
            n += 1

    return result

def insert_expression(array=[], level=0, after=0, operator='|', expr=None):
        
    result = []
    if len(array) == 0:
        result.append(expr)
        return result
    
    n = -1
    count = -1
    tree = []

    inserted = False
    for a in array:
        if count == level and n == after: 
            tree.insert(count-n, [operator])
            
            count += 1
            tree[count].insert(n+1, expr)
            
            n += 2
            tree[count].append(a)
            inserted = True
        elif '&' in a or '|' in a:
            n = -1
            count += 1
            tree.append([a])
        else: 
            n += 1
            if count < 0: 
                count += 1
                tree.append([])
            tree[count].append(a)
    
    if not inserted: 
        tree.insert(level-after, [operator])
        tree[level+1].insert(after+1, expr)

    for t in tree:
        for e in t:
            result.append(e)
    
    return result

def export_helper(self, fields, BaseModel, collections, _is_toplevel_call=True):
    """ Export fields of the records in ``self``.

        :param fields: list of lists of fields to traverse
        :param bool _is_toplevel_call:
            used when recursing, avoid using when calling from outside
        :return: list of lists of corresponding values
    """
    import_compatible = self.env.context.get('import_compat', True)
    lines = []

    def splittor(rs):
        """ Splits the self recordset in batches of 1000 (to avoid
        entire-recordset-prefetch-effects) & removes the previous batch
        from the cache after it's been iterated in full
        """
        for idx in range(0, len(rs), 1000):
            sub = rs[idx:idx+1000]
            for rec in sub:
                yield rec
            rs.invalidate_cache(ids=sub.ids)
    if not _is_toplevel_call:
        splittor = lambda rs: rs

    # memory stable but ends up prefetching 275 fields (???)
    for record in splittor(self):
        # main line of record, initially empty
        current = []
        current.append([''] * len(fields))
        names = []

        # list of primary fields followed by secondary field(s)
        primary_done = []
        if len(list(filter(lambda x: 'product_id' in x, fields))) > 0:
            if record['product_id'] and record['product_id']['product_tmpl_id'] and record['product_id']['product_tmpl_id']['internal_ref_ids']:
                iris = record['product_id']['product_tmpl_id']['internal_ref_ids']
                for iri in iris:
                    names.append(iri['name'])
                    current.append([''] * len(fields))
        
        for c in current:
            lines.append(c)

        # process column by column
        for i, path in enumerate(fields):
            if not path:
                continue

            name = path[0]
            if name in primary_done:
                continue

            if name == '.id':
                for j in range(len(current)):
                    current[j][i] = str(record.id)
            elif name == 'id':
                for j in range(len(current)):
                    current[j][i] = (record._name, record.id)
            else:
                field = record._fields[name]
                value = record[name]

                # this part could be simpler, but it has to be done this way
                # in order to reproduce the former behavior
                if not isinstance(value, BaseModel):
                    for j in range(len(current)):
                        current[j][i] = field.convert_to_export(value, record)
                else:
                    primary_done.append(name)

                    # in import_compat mode, m2m should always be exported as
                    # a comma-separated list of xids in a single cell
                    if import_compatible and field.type == 'many2many' and len(path) > 1 and path[1] == 'id':
                        xml_ids = [xid for _, xid in value.__ensure_xml_id()]
                        for j in range(len(current)):
                            current[j][i] = ','.join(xml_ids) or False
                        continue

                    # recursively export the fields that follow name; use
                    # 'display_name' where no subfield is exported
                    fields2 = [(p[1:] or ['display_name'] if p and p[0] == name else [])
                                for p in fields]
                    lines2 = value._export_rows(fields2, _is_toplevel_call=False)
                    if lines2:
                        # merge first line with record's main line
                        for j, val in enumerate(lines2[0]):
                            if val or isinstance(val, bool):
                                for x in range(len(current)):
                                    if name == 'product_id' and x > 0:
                                        current[x][j] = names[x-1]
                                    else:
                                        current[x][j] = val
                                    
                        # append the other lines at the end
                        lines += lines2[1:]
                    else:
                        for j in range(len(current)):
                            current[j][i] = False

    # if any xid should be exported, only do so at toplevel
    if _is_toplevel_call and any(f[-1] == 'id' for f in fields):
        bymodels = collections.defaultdict(set)
        xidmap = collections.defaultdict(list)
        # collect all the tuples in "lines" (along with their coordinates)
        for i, line in enumerate(lines):
            for j, cell in enumerate(line):
                if type(cell) is tuple:
                    bymodels[cell[0]].add(cell[1])
                    xidmap[cell].append((i, j))
        # for each model, xid-export everything and inject in matrix
        for model, ids in bymodels.items():
            for record, xid in self.env[model].browse(ids).__ensure_xml_id():
                for i, j in xidmap.pop((record._name, record.id)):
                    lines[i][j] = xid
        assert not xidmap, "failed to export xids for %s" % ', '.join('{}:{}' % it for it in xidmap.items())

    return lines

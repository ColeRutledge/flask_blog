from flask import current_app


def add_to_index(index, model):
    '''
    can be used to add and update from elastic. will check for existence of
    elastic config. if it exists, it will create a payload dict by creating
    keys from the __searchable__ fields and values from the corresponding
    fields on the db model. following that, it will index them in elastic.
    ex: -> payload = {'body': 'this post will be indexed'}

    :param index:       name of the index to be added. refers to __tablename__
                        from the model obj (e.g. - Post)
    :param model:       sqlalchemy session object that needs to be indexed
    :returns:
    '''
    if not current_app.elasticsearch:
        return

    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)

    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    '''
    will check for existence of elastic config. if it exists, it will use the
    index name and the model.id to delete the index from the database

    :param index:       name of the index to be added. refers to __tablename__
                        from the model obj (e.g. - Post)
    :param model:       sqlalchemy session object that needs to be indexed
    :returns:
    '''
    if not current_app.elasticsearch:
        return

    # using the same unique id in both elastic and sqlalchemy makes
    # this lookup convenient by being able to reference the model.id
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    '''
    will check for existence of elastic config. if it exists,

    :param index:       name of the index to be added. refers to __tablename__
                        from the model obj (e.g. - Post)
    :param query:       search string to be queried from elastic
    :param page:        refers to page number. used for returning the correct results based
                        on pagination
    :param per_page:    results per page to allow calculation for proper pagination results
    :returns:           tuple -> (lst(model.ids), int(num_of_results))
                        if no elastic config, will return tuple with empty list and 0, otherwise,
                        will return a list of model.ids found and total number of results
    '''
    if not current_app.elasticsearch:
        return [], 0

    search = current_app.elasticsearch.search(
        index=index,
        body={
            # multi_match can search across multiple fields, or in
            # this case, the entire index. allows function to be
            # generic as different models can have different field names
            'query': {'multi_match': {'query': query, 'fields': ['*']}},
            # from and size arguments allow for pagination/subset calculation
            'from': (page - 1) * per_page, 'size': per_page,
        }
    )
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']

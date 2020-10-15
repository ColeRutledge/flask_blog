from flask import current_app


def add_to_index(index, model):
    if not current_app.elasticsearch:
        return

    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)

    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return

    # using the same unique id in both elastic and sqlalchemy makes
    # this lookup convenient by being able to reference the model.id
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0

    search = current_app.elasticsearch.search(
        index=index,
        body={
            # multi-match can search across multiple fields
            'query': {'multi_match': {'query': query, 'fields': ['*']}},
            # from and size arguments allow for pagination
            'from': (page - 1) * per_page, 'size': per_page,
        }
    )
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']

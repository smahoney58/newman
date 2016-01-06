import itertools
import tangelo

def _terms_filter(field='', values=[]):
    return [] if (not field or not values) else [{"terms" : { field : values}}]

# address_filter_mode = "union"|"intersect" , union will match any emails with any of the addresses, intersect will match the sender AND any rcvr addresses
def _addrs_filter(senders=[], tos=[], ccs=[], bccs=[], address_filter_mode="union"):
    if address_filter_mode=="intersect":
        addrs = _terms_filter("tos", tos) + _terms_filter("ccs", ccs) + _terms_filter("bccs", bccs)
        return {
            "bool":{
                "should":[addrs],
                "must":[_terms_filter("senders", senders)],
                "must_not":[]
            }
        }
    else:
        addrs = _terms_filter("senders", senders) + _terms_filter("tos", tos) + _terms_filter("ccs", ccs) + _terms_filter("bccs", bccs)
        return {
            "bool":{
                "should":[addrs],
                "must":[],
                "must_not":[]
            }
        }

# Expects entity_map to be of the form
# {"entities.entity_person":[],"entities.entity_location":[],"entities.entity_organization":[],"entities.entity_misc":[]}
# Or whatever keys match the current entity style
def _entity_filter(entity_dict=[]):
    return list(itertools.chain(*[_terms_filter(k,v) for k,v in entity_dict.iteritems()]))

def _date_filter(date_bounds=None):
    return [] if not date_bounds else [{"range" : {"datetime" : { "gte": str(date_bounds[0]), "lte": str(date_bounds[1])}}}]

def _date_filter_not_equal(date_bounds=None):
    return [] if not date_bounds else [{"range" : {"datetime" : { "gt": str(date_bounds[0]), "lt": str(date_bounds[1])}}}]

# TODO how do we apply the query_terms as a filter?  Seems that it makes sense to do this as a query only but
# TODO it is possible we will want to use a term filter on "_all"
# address_filter_mode = "union"|"intersect" , union will match any emails with any of the addresses, intersect will match the sender AND any rcvr addresses
def _build_filter(email_senders=[], email_rcvrs=[], query_terms='', topic_score=None, entity_dict={}, date_bounds=None, date_mode_inclusive=True, address_filter_mode="union"):

    # One of these addresses should apear on the email
    address_filter = [] if (not email_senders or not email_rcvrs) else [_addrs_filter(email_senders,email_rcvrs,email_rcvrs,email_rcvrs, address_filter_mode=address_filter_mode)]
    tangelo.log("====================================(query: %s)" % (address_filter))

    query_terms_filter = [] if not query_terms else _terms_filter("_all", query_terms.split(" "))

    date_range = _date_filter(date_bounds) if date_mode_inclusive else  _date_filter_not_equal(date_bounds)

    topic_range= [] if not topic_score else [{"range" : {"topic_scores.idx_"+str(topic_score[0]) : { "gte": topic_score[1]}}}]

    entity_filter = [] if (not entity_dict) else _entity_filter(entity_dict)


    filter =  {
        "bool":{
            "should":[],
            "must":[],
            "must_not":[]
        }
    }

    bool_filter = filter["bool"]
    bool_filter["must"] += address_filter

    bool_filter["must"] += date_range
    bool_filter["must"] += topic_range
    bool_filter["must"] += entity_filter
    tangelo.log("====================================2(query: %s)" % (bool_filter))

    # This needs to occur last as it adds a default search filter if none is available
    if not (bool_filter["must"] or bool_filter["should"] or bool_filter["must_not"]) :
        bool_filter["must"].append({"match_all":{}})
    tangelo.log("====================================3(query: %s)" % (filter))

    return filter

# build an es filter based on emails, date bounds (start, end) and terms which should be a phrase or terms in a single
# String
# topic_score = (<idx>, <score>) returns docs with topic idx=<idx> and score >= <score>
# date_mode will control if the date bounds uses gte / lte or gt/lt values are ("inclusive", "exclusive")
# send_addrs or recipient_addrs are provided they will be used instead of email_addrs for the respective parts of the query
# address_filter_mode = "union"|"intersect" , union will match any emails with any of the addresses, intersect will match the sender AND any rcvr addresses
def _build_email_query(email_addrs=[], sender_addrs=[], recipient_addrs=[], query_terms='', topic_score=None, entity={}, date_bounds=None, sort_order="acs", date_mode_inclusive=True, address_filter_mode="union"):

    term_query = {"match_all" : {}} if not query_terms else {"match" : {"_all" : query_terms}}

    sender_addrs = email_addrs if not sender_addrs else sender_addrs
    recipient_addrs = email_addrs if not recipient_addrs else recipient_addrs

    query_email_addr =  {
        "query" : {
            "filtered" : {
                "query" : term_query,
                "filter" :  _build_filter(email_senders=sender_addrs, email_rcvrs=recipient_addrs, topic_score=topic_score, entity_dict=entity, date_bounds=date_bounds, date_mode_inclusive=date_mode_inclusive, address_filter_mode=address_filter_mode)
            }
        },
        "sort":  {} if not term_query else { "datetime": { "order": sort_order }}
        # Multilevel sort
        #     "sort": [
        #     { "_score": { "order": "desc" }},
        #     { "datetime": { "order": "desc" }}
        # ]
    }
    return query_email_addr

# Build a query for sender email attachments
def _build_email_attachment_query(sender_address, query_terms='', topic_score=None, entity={}, date_bounds=None, sort_order="acs", date_mode_inclusive=True):

    term_query = {"match_all" : {}} if not query_terms else {"match" : {"_all" : query_terms}}

    query_email_addr =  {
        "filter":{"exists":{"field":"attachments"}},
        "query" : {
            "filtered" : {
                "query" : term_query,
                "filter" :  _build_filter(email_senders=[sender_address], topic_score=topic_score, entity_dict=entity, date_bounds=date_bounds, date_mode_inclusive=date_mode_inclusive)
            }
        },
        "sort":  {} if not term_query else { "datetime": { "order": sort_order }}
        # Multilevel sort
        #     "sort": [
        #     { "_score": { "order": "desc" }},
        #     { "datetime": { "order": "desc" }}
        # ]
    }
    return query_email_addr
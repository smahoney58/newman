import json

import tangelo
import cherrypy

from newman.settings import getOpt
from es_email import get_ranked_email_address, get_attachment, get_attachments_sender, get_email, get_domain
from newman.newman_config import getDefaultDataSetID
from param_utils import parseParamDatetime


#GET /email/<id>
# deprecated slated for removal
def getEmail(*args, **kwargs):
    tangelo.log('getEmail(%s)' % str(args));
    data_set_id, start_datetime, end_datetime, size = parseParamDatetime(**kwargs)

    return get_email(*args, **kwargs)


#GET /rank
# deprecated slated for removal
def getRankedEmails(*args, **kwargs):
    tangelo.log("getRankedEmails(args: %s kwargs: %s)" % (str(args), str(kwargs)))
    data_set_id, start_datetime, end_datetime, size = parseParamDatetime(**kwargs)

    return get_ranked_email_address(*args, **kwargs)

# DEPRECATED  TODO remove
#GET /target
#deprecated; use new service url http://<host>:<port>/datasource/all/
def getTarget(*args, **kwargs):
    target = getOpt('target')

    tangelo.content_type("application/json")
    return { "email" : []}

#GET /domains
def getDomains(*args, **kwargs):
    tangelo.log("getDomains(args: %s kwargs: %s)" % (str(args), str(kwargs)))
    tangelo.content_type("application/json")
    data_set_id, start_datetime, end_datetime, size = parseParamDatetime(**kwargs)
    return get_domain(data_set_id)

#GET /attachments/<sender>
def getAttachmentsSender(*args, **kwargs):
    tangelo.log("getAttachmentsSender(args: %s kwargs: %s)" % (str(args), str(kwargs)))
    data_set_id, start_datetime, end_datetime, size = parseParamDatetime(**kwargs)

    return get_attachments_sender(*args, **kwargs)

# DEPRECATED TODO remove me
#GET /exportable
def getExportable(*args, **kwargs):
    tangelo.content_type("application/json")
    return { "emails" : []}

# DEPRECATED TODO remove me
#POST /exportable
def setExportable(data):
    tangelo.content_type("application/json")
    return { "email" : {} }

# DEPRECATED TODO remove me
#POST /exportmany
def setExportMany(data):
    tangelo.content_type("application/json")
    return { 'exported' : []}

# DEPRECATED TODO remove me
#POST /download
def buildExportable(*args):
    return { "file" : "downloads/{}.tar.gz".format("NONE") }

get_actions = {
    "target" : getTarget,
    "email" : getEmail,
    "domains" : getDomains,
    "rank" : getRankedEmails,
    "exportable" : getExportable,
    "download" : buildExportable,
    "attachment" : get_attachment,
    "attachments" : getAttachmentsSender

}

post_actions = {
    "exportable" : setExportable,
    "exportmany" : setExportMany
}

def unknown(*args):
    return tangelo.HTTPStatusCode(400, "invalid service call")

@tangelo.restful
def get(action, *args, **kwargs):

    cherrypy.log("email(args[%s] %s)" % (len(args), str(args)))
    cherrypy.log("email(kwargs[%s] %s)" % (len(kwargs), str(kwargs)))

    if ("data_set_id" not in kwargs) or (kwargs["data_set_id"] == "default_data_set"):
        kwargs["data_set_id"] = getDefaultDataSetID()

    return get_actions.get(action, unknown)( *args, **kwargs)

@tangelo.restful
def post(*pargs, **kwargs):
    post_data = json.loads(cherrypy.request.body.read())
    path = '.'.join(pargs)
    return post_actions.get(path, unknown)(post_data)

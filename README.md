CouchDB Integration
------
This proxy expects each CouchDB document to contain a dict called authLayer.

The authLayer dict is expected to contain a number of key:value pairs, where the key is a HTTP request method, and the value is a list of sessions that are allowed access.

("ANY" is an additional key, which will match any HTTP request method).

For example, a document setup for authLayer might look like this:
```
{
   "_id": "ExampleDocument",
   "_rev": "1234567890",
   "authLayer": {
       "GET": [
           {
               "oauth2_provider": "github.com",
               "oauth2_uid": 2345678,
               "ouath2_nickname": "jane-doe"
           },
           {
               "oauth2_provider": "github.com",
               "oauth2_uid": 3456789,
               "ouath2_nickname": "john-smith"
           }
       ],
       "ANY": [
           {
               "oauth2_provider": "github.com",
               "oauth2_uid": 1234567,
               "ouath2_nickname": "ben-albon"
           }
       ]
   }
}
```
In this example, jane-doe and john-smith would be allowed to GET the document, but only ben-albon would be allowed to POST changes to the document.

SessionDB Integration
------
This proxy is specifically written to integrate with my [PHP-PostgreSQL-Session-Handler fork](https://github.com/ben-albon/PHP-PostgreSQL-Session-Handler).

If I had more time to dedicate to it, I would have abstracted the session handling into a separate module (to allow for extensibility).

The proxy itself requires only a dict of session_data relating to the provided HTTP cookie.  The elements in the CouchDB ACL (see above) are then compared against this session_data dict.  If all elements in the ACL match the corresponding elements in the session_data, then access is granted.  If any element does not match, then access is denied.

This gives room for a lot of flexibility in access control.  For example, the following document allows GET requests from all sessions authenticated using github.com (regardless of user):
```
{
   "_id": "ExampleDocument",
   "_rev": "1234567890",
   "authLayer": {
       "GET": [
           {
               "oauth2_provider": "github.com"
           }
       ]
   }
}
```
I welcome any pull request that extends this proxy to work with other session handlers :-)

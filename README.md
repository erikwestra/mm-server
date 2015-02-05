# `mmServer` #

`mmServer` is a Django project that implements the server-side logic for the
MessageMe system.  The `mmServer` system provides a simple API that allows for
the following server-side functionality:

 * Creating, updating and retrieving a user's own profile.
<br/><br/>
 * Viewing the publically-visible parts of another user's profile.
<br/><br/>
 * Storing, retrieving and updating profile pictures.
<br/><br/>
 * Storing the encryption key used by a conversation between two users.

Additional functionality may be added in the future.


## User Profiles ##

Each user is identified by their **Global ID** value.  A user has a profile
associated with their global ID.  In the API, the profile is represented by an
object with the following attributes:

> `global_id`
> 
> > The global ID for the owner of this profile.
> 
> `deleted`
> 
> > Has this profile been deleted?
> 
> `name`
> 
> > The name of the profile's owner, as entered by the user.
> 
> `name_visible`
> 
> > A boolean indicating whether the profile name is visible to other users.
> 
> `location`
> 
> > The location of the profile's owner, as entered by the user.
> 
> `location_visible`
> 
> > A boolean indicating whether the profile location is visible to other
> > users.
> 
> `picture_id`
> 
> > The ID of the profile picture uploaded by the user, if any.
> 
> `picture_visible`
> 
> >  A boolean indicating whether the profile picture is visible to other
> >  users.

Note that the profile object returned by the API will only contain the
publically-visible portions of the profile if the user is attempting to view
another user's profile.


## Profile Pictures ##

A profile picture is simply an image file which is uploaded to the `mmServer`
and can be retrieved later on.  Each picture is identified by a unique
**Picture ID**.

In the API, a picture is represented by an object with the following fields:

> `picture_id`
> 
> > The unique ID for this picture.
> 
> `deleted`
> 
> > Has this picture been deleted by the user?
> 
> `account_secret`
> 
> > The account secret of the user who created this picture.  This ensures that
> > nobody other than the creator can update or delete a picture.
> 
> `filename`
> 
> > The filename of the uploaded picture.
> 
> `contents`
> 
> > The contents of the picture.  Note that you must explicitly retrieve the
> > picture to download the contents -- the polling system only returns the
> > other information about the picture.


## Conversations ##

A **conversation** is a record of the conversation between two users.  Each
pair of users will have exactly one conversation record; you cannot have two
conversations for the same pair of users.

In the API, a conversation is represented internally by an object with the
following fields:

> `global_id_1`
> 
> > The global ID of the first user in the conversation.  This will be the ID
> > of the user who initiated the conversation.
> 
> `global_id_2`
> 
> > The global ID of the second user in the conversation.
> 
> `encryption_key`
>
> > A string used to encrypt messages between these two users.
> 
> `hidden_1`
> 
> > Has the first user hidden this conversation?
> 
> `hidden_2`
> 
> > Has the second user hidden this conversation?
> 
> `last_message`
> 
> > The text of the last message sent for this conversation.  If there are no
> > messages in this conversation, this will be set to a `null` value.
> 
> `last_timestamp`
> 
> > The date and time when the last message was sent for this conversation, as
> > a unix timestamp value in UTC.  If there are no messages in this
> > conversation, this will be set to `null`.
> 
> `num_unread_1`
> 
> > The number of messages the first user has not yet seen in this
> > conversation.  This is calculated based on the current status of the
> > messages sent to this user.
> 
> `num_unread_2`
> 
> > The number of messages the second user has not yet seen in this
> > conversation.  This is calculated based on the current status of the
> > messages sent to this user.

Note that the conversation is **adapted** to match the viewpoint of the current
user.  That is, if the current user's global ID matches `global_id_1`, then the
API will return the following set of fields back to the caller:

>     global_id_1    => my_global_id
>     global_id_2    => their_global_id
>     hidden_1       => hidden
>     last_message   => last_message
>     last_timestamp => last_timestamp
>     num_unread_1   => num_unread

Conversely, if the current user's global ID matches `global_id_2`, then the API
will return the following set of fields back to the caller:

>     global_id_2    => my_global_id
>     global_id_1    => their_global_id
>     hidden_2       => hidden
>     last_message   => last_message
>     last_timestamp => last_timestamp
>     num_unread_2   => num_unread

This ensures that each user sees the conversation from their particular point
of view, while still having a single global conversation record for both users.


## Messages ##

A **message** is the unit of communication between users.  Messages can be
freeform text, or they can include **actions** that need to be performed.
Within the API, a message consists of the following information:

> `conversation`
> 
> > A link to the conversation this message is part of.
> 
> `hash`
> 
> > A string uniquely identifying this message.
> 
> `timestamp`
> 
> > The date and time when this message was sent, as a unix timestamp value in
> > UTC.
> 
> `sender_global_id`
> 
> > The global ID of the user who sent this message.
> 
> `recipient_global_id`
> 
> > The global ID the user who received this message.
> 
> `sender_account_id`
> 
> > The Ripple account ID of the user who sent this message.
> 
> `recipient_account_id`
> 
> > The Ripple account ID of the user who received this message.
> 
> `text`
> 
> > The text of the message.
> 
> `action`
> 
> > The action associated with this message.  The following actions are
> > currently supported:
> > 
> > > `SEND_XRP`
> > > 
> > > > Send some XRP to the other user.
> > > 
> > > `REQUEST_XRP`
> > > 
> > > > Request some XRP from the other user.
> > 
> > If the message does not have an action associated with it, the `action`
> > field will be set to a `null` value.

> `action_params`
> 
> > A dictionary mapping action parameter names to their associated values,
> > converted to a JSON-format string.  The exact set of parameters depends on
> > the action being performed, as described below.
> > 
> > * For the `SEND_XRP` action:
> >  
> > > > `amount`
> > > > 
> > > > > The amount to send, as an integer number of drops.
> > 
> > * For the `REQUEST_XRP` action:
> > 
> > > > `amount`
> > > > 
> > > > > The amount to request, as an integer number of drops.
> > 
> > If the message does not have any action parameters, the `action_params`
> > field will be set to a `null` value.
> 
> `action_processed`
> 
> > Has this action been processed by the recipient?
> 
> `amount_in_drops`
> 
> > The amount to send to the recipient of this message, as an integer number
> > of drops.  If this is not specified, the message will have an amount of 1
> > drop.  Note that the minimum that can be sent is 1 drop.
> 
> `status`
> 
> > The message's current status.  This can be one of the following strings:
> > 
> > > `PENDING`
> > > 
> > > > The message has been submitted to the Ripple network, but the
> > > > underlying transaction has not yet gone through.
> > > 
> > > `SENT`
> > > 
> > > > The message has been sent successfully.
> > > 
> > > `READ`
> > > 
> > > > The message has been read by the recipient.
> > > 
> > > `FAILED`
> > > 
> > > > The message could not be sent for some reason.
> 
> `error`
> 
> > If the message could not be sent, this will be a string describing what
> > went wrong.


## Authentication ##

To ensure that a user can only view or update the information they're supposed
to have access to, we use Hash-based Message Authentication (HMAC) based on the
account secret.  Before making a request that requires authentication, the
client should do the following:

 1. Calculate a unique "nonce" value.  This can be done, for example, by
    generating a UUID value as a 36-character string.  The resulting string
    should be called **NONCE-STRING**.
<br/><br/>
 2. Calculate an MD5 hash of the request body.  Note that the body of the
    request will be an empty string for HTTP `GET` requests.  The resulting MD5
    hash should be called **CONTENT-MD5**.
<br/><br/>
 3. Calculate the HMAC digest for this request by concatenating together the
    following values, with a newline character between each value:

    * The HTTP method being used.
    * The URL for the desired API request, excluding the server name and any
      query-string parameters.
    * The calculated Content-MD5 value.
    * The nonce value.
    * The user's account secret.

    The concatenated string is then used to calculate an SHA-1 digest, which is
    then converted to base64 encoding.  The result should be called the
    **HMAC-AUTH-STRING**.
<br/><br/>
 4. Finally, the HTTP request is made, with the following headers included in
    the request:

> > Authorization: HMAC **`HMAC-AUTH-STRING`**  
> > Content-MD5: **`CONTENT-MD5`**  
> > Nonce: **`NONCE-STRING`**  

Since the account secret is also stored on the server, the server can
calculate its own version of the HMAC digest and compare it against the digest
sent by the client.  The request will be rejected if (a) the calculated HMAC
digests don't match, or (b) if the nonce value has been used previously.


## Change Detection ##

The `mmServer` API supports clients polling for changes.  The following
information can be polled for:

 * New and updated user profiles.
 * New and updated profile pictures.
 * New and updated conversations.
 * New and updated messages.

Polling always returns only the information relevant to the currently signed-in
user.  If the user is not signed in, no polling should be attempted.

Polling uses the concept of an **anchor**.  The anchor is a string that
identifies a particular state of the data.  If the client does not have an
anchor value, calling the `GET api/changes` endpoint will return just the
anchor value that represents the current state of the server.  The client
should wait a few seconds before making another call to the `GET api/changes`
endpoint, this time supplying the current anchor value.  The API will return
any changes which have been made since the previous state of the system, along
with an updated anchor value that represents the new state of the system.

Polling should be done once every 3-5 seconds.  In this way, the client can be
kept up-to-date with all changes that occur to the profiles, pictures,
conversations and messages.


## API Endpoints ##

The `mmServer` API supports a number of endpoints, all of which are documented
below.  These are grouped by resource to make it easier to find the endpoint
you are looking for.


### Endpoints for the Profile Resource ###

**`GET api/profiles`**

Retrieve a list of user profiles matching a given search criteria.  This
request does not use HMAC authentication.   The following query-string
parameters are supported:

> `name`
> 
> > The name of the profile to search for.  The API will find all profiles
> > with a name starting with the given string.
> 
> `page`
> 
> > The page number of results to return.  This defaults to 1 if no page number
> > is supplied.

Upon completion, this API endpoint will return an HTTP response code of 200
(OK).  The body of the response will be a string containing the search results
as a JSON-formatted object.  If the search request was successful, this object
will have the following fields:

>     {success: true,
>      num_pages: 999,
>      profiles: [{global_id:"...", name:"..."}, ...]
>     }

As you can see, each item in the `profiles` array is an object holding the
global ID and profile name for the matching profile.

Because the search can potentially return a large number of results, the
response is *paginated*; that is, only up to 50 matching profiles will be
returned at once.  The `num_pages` value tells you how many pages of profiles
were found, and you can re-issue the request with a `page` parameter to
retrieve additional pages of results.

If the search request failed, the API will still return an HTTP response code
of 200 (OK).  In this case, the body of the response will be a JSON-formatted
object that looks like the following:

>     {success: true,
>      error: "..."
>     }

In this case, `error` will be a string describing why the search request
failed.

> _**Note**: This API endpoint only finds profiles which match the given name,
> and which have made their profile name public._

**`GET api/profile/<GLOBAL-ID>`**

Retrieve a user's profile.  If the HTTP request does not include HMAC
authentication, only the public details for the given profile will be returned.
Otherwise (assuming the authentication digest matched the details for the given
user), all of the profile's contents will be returned.

Upon successful completion, this API endpoint will return an HTTP response code
of 200 (OK).  The body of the response will be a string containing the returned
user profile as a JSON-formatted object.  The returned profile object will
contain either the publically-visible portion of the user's profile (if the
user is viewing another user's profile), or the full profile details if the
user is authenticated as the owner of the profile.

If there is no profile data for the given user, the API endpoint will return an
HTTP response code of 404 (Not Found).

If the caller is attempting to use HMAC authentication to get the user's full
profile, and the authentication failed, the API endpoint will return an HTTP
response code of 403 (Forbidden).

**`POST api/profile/<GLOBAL-ID>`**

Create a user's profile.  This request must use HMAC authentication.  The body
of the request should be a JSON-formatted string containing the following:

>     {account_secret: "...",
>      profile: {...}
>     }

A new profile with the given details will be created.  Note that this is the
only time the account secret ever sent to the server -- we need this to create
the profile and support HMAC authentication for future API requests (and also
to verify this request's HMAC authentication digest).

Upon completion, the API endpoint will return a HTTP response code of 201
(Created) if the profile was successfully created.  If a profile already exists
for this user, the API endpoint will return an HTTP response code of 409
(Conflict).  If the HMAC authentication details are missing or invalid, the API
endpoint will return an HTTP response code of 403 (Forbidden).

**`PUT api/profile/<GLOBAL-ID>`**

Update a user's profile.  This request must use HMAC authentication.  The body
of the request should be a JSON-formatted string containing the profile details
to update.  Note that any fields not included in the profile object will not be
updated -- this allows you to only send the changes that you want to make to
the user's profile.

Upon completion, the API endpoint will return an HTTP response code of 200 (OK)
if the user's profile was successfully updated.  If the HMAC authentication
details are missing or invalid, the API endpoint will return an HTTP response
code of 403 (Forbidden).

**`DELETE api/profile/<GLOBAL-ID>`**

Delete a user's profile.  This request must be HMAC authentication.  No data
needs to be included in the body of the request.

Upon completion, the API endpoint will return an HTTP response code of 200 (OK)
if the user's profile was successfully deleted.  If the HMAC authentication
details are missing or invalid, the API endpoint will return an HTTP response
code of 403 (Forbidden).


### Endpoints for the Picture Resource ###

**`GET api/picture/<PICTURE-ID>`**

Retrieve a profile picture with the given ID.

If there is a picture with the given ID, the picture's image data will be
returned.  If there is no picture with that ID, the API endpoint will return an
HTTP response code of 404 (not found).

Note that this API endpoint does not require any HMAC authentication; pictures
can always be downloaded if you know the ID.

**`POST api/picture`**

Upload a new picture to the server.  This request must include HMAC
authentication.  The body of the request should be a string containing the
following JSON-format object:

>     {account_secret: "...",
>      picture_filename: "...",
>      picture_data: "..."
>     }

where `account_secret` is the account secret to use for uploading this image,
`picture_filename` is the name of the file (in particular, including the file
extension for this type of image), and `picture_data` is the raw contents of
the picture, converted to a base64-format string.

Upon completion, the API endpoint will return a HTTP response code of 201
(Created) if the picture was successfully uploaded, and the body of the
response will be a string containing the picture ID for the newly-uploaded
picture.  If the HMAC authentication details are missing or invalid, the API
endpoint will return an HTTP response code of 403 (Forbidden).

**`PUT api/picture/<PICTURE-ID>`**

Update an existing picture on the server.  This API endpoint must use HMAC
authentication.  The body of the request should be a string containing the
following JSON-format object:

>     {picture_filename: "...",
>      picture_data: "..."
>     }

The fields have the same meaning as for the **`POST`** endpoint, above.  Note
that the picture can only be updated if the `account_secret` in the HMAC header
matches the account secret used when the picture was first created.

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the picture was successfully updated.  If the HMAC authentication
details are missing or invalid, the API endpoint will return an HTTP response
code of 403 (Forbidden).

**`DELETE api/picture/<PICTURE-ID>`**

Delete a picture from the server.  This API endpoint must use HMAC
authentication.  No additional data is needed in the body of the request.  Note
that the picture can only be deleted if the `account_secret` in the HMAC header
matches the account secret used when the picture was first created.

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the picture was successfully deleted.  If the HMAC authentication details
are missing or invalid, the API endpoint will return an HTTP response code of
403 (Forbidden).


### Endpoints for the Conversation Resource ###

**`GET api/conversations/<GLOBAL-ID>`**

Return a list of the current user's conversations.  This API endpoint must use
HMAC authentication.

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing the following JSON-format object:

>     {conversations: [
>          {my_global_id: "...",
>           their_global_id: "...",
>           hidden: false,
>           last_message: "...",
>           last_timestamp: 1420173182,
>           num_unread: 0},
>          ...
>      ]
>     }

Each entry in the `conversations` list is an object with the details of the
conversation, adapted to the viewpoint of the current user, as described
in the section on conversations, above.  The conversations will be sorted in
descending order of their `last_timestamp` value.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If there is no user
profile for the given global ID, the API endpoint will return an HTTP response
code of 404 (Not Found).

**`GET api/conversation`**

Retrieve a single conversation between this user and somebody else.  This API
endpoint must use HMAC authentication.  The following query-string parameters
are required:

> `my_global_id`
> 
> > The current user's global ID.
> 
> `their_global_id`
> 
> > The other user's global ID.

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing the following JSON-format object:

>     {conversation:
>          {my_global_id: "...",
>           their_global_id: "...",
>           hidden: false,
>           last_message: "...",
>           last_timestamp: 1420173182,
>           num_unread: 0}
>     }

The `conversation` object will contain the details of the conversation between
the two users, adapted to the viewpoint of the current user as described in the
section on conversations, above.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If there is no
conversation between these two users, the API endpoint will return an HTTP
response code of 404 (Not Found).

**`POST api/conversation`**

Start a new conversation between this user and someobdy else.  This API
endpoint must use HMAC authentication.  The body of the request should be a
string containing the following JSON-format object:

>     {my_global_id: "...",
>      their_global_id: "..."
>     }

`my_global_id` is the global ID of the current user, and `their_global_id` is
the global ID of the other person to start the conversation with.

> _**Note:** the current user must have an existing profile for this API
> endpoint to work._

Upon completion, this API endpoint will return an HTTP response code of 201
(Created) if the conversation was successfully created.  If the HMAC
authentication details are missing or invalid, the API endpoint will return an
HTTP response code of 403 (Forbidden).  If there is already a conversation
record for this pair of users, the API endpoint will return an HTTP response
code of 409 (Conflict).  In all cases, the body of the response will be empty.

**`PUT api/conversation`**

Update the conversation between this user and somebody else.  This API endpoint
must use HMAC authentication.  The body of the request should be a string
containing the following JSON-formatted object:

>     {my_global_id: "...",
>      their_global_id: "...,
>      action: "..."
>     }

The `action` string indicates how the conversation should be updated.
Additional fields may be included in the request object as required to complete
the action.

The following actions are currently supported:

> `HIDE`
> 
> > Hide this conversation for this user.  The conversation will no longer
> > appear in the user's list of conversations.
> 
> `UNHIDE`
> 
> > Unhide this conversation for this user.  The conversation will once again
> > appear in the user's list of conversations.

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the conversation was succesfully updated.  If there is a problem with
the request parameters, the API endpoint will return an HTTP response code of
400 (Bad Request).  If the HMAC authentication details are missing or invalid,
the API endpoint will return an HTTP response code of 403 (Forbidden).  If
there is no conversation between these two users, the API endpoint will return
an HTTP response code of 409 (Conflict).  In all cases, the body of the
response will be empty.

More actions may be added in the future as they are needed.


### Endpoints for the Message Resource ###

**`GET api/messages`**

Obtain a list of messages.  This API endpoint must use HMAC authentication.
The following query-string parameters are supported:

> `my_global_id` _(required)_
> 
> > The current user's global ID.
> 
> `their_global_id` _(optional)_
> 
> > The other user's global ID.

> _**Note**: the current user must have an existing profile for this API
> endpoint to work._

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing the following JSON-format object:

>     {messages: [
>          {hash: "...",
>           timestamp: 1420173182,
>           sender_global_id: "...",
>           recipient_global_id: "...",
>           sender_account_id: "...",
>           recipient_account_id: "...",
>           text: "...",
>           action: "...",
>           action_params: "...",
>           amount_in_drops: 100,
>           status: "...",
>           error: "..."},
>          ...
>      ]
>     }

Each entry in the `messages` list is an object with the details of the message,
as described in the Messages section, above.  The `error` field will only be
present if the message failed to be sent.

If the `their_global_id` parameter was supplied, only messages between the two
users will be returned.  Otherwise, all messages sent to or received by the
current user will be returned.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If there is no user
profile for either of the supplied global ID values, the API endpoint will
return an HTTP response code of 404 (Not Found).

**`POST api/message`**

Attempt to send a message.  This API endpoint must use HMAC authentication.
The body of the request should be a string containing the following JSON-format
object:

>     {message: {
>           sender_global_id: "...",
>           recipient_global_id: "...",
>           sender_account_id: "...",
>           recipient_account_id: "...",
>           text: "...",
>           action: "...",
>           action_params: "...",
>           amount_in_drops: 100}
>     }

**_Note_**:
 
> * The sending user must have an existing profile for this API endpoint to
>   work.
> <br/><br/>
> * The `action` and `action_params` fields are only required if the message
>   has an action associated with it.
> <br/></br>
> * The `amount_in_drops` field is only needed if you wish to send funds
>   along with the message.

If the message was accepted, the API endpoint will return an HTTP response code
of 202 (Accepted).  If the message was rejected right away, the API endpoint
will return an HTTP response code of 400 (Bad Request), and the body of the
response will be a string containing the error returned by the Ripple server.

Note that the message will initially be given a status of "PENDING".  The
server will then monitor the message, and update the message status as
appropriate depending on what happens to the message.  The various status
values for the message will all be received if the client is polling for
message updates.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If some required fields
are missing, the API will return a response code of 400 (Bad Request).

**`PUT api/message`**

Update a message.  This API endpoint must use HMAC authentication.  The body of
the request should be a string containing the following JSON-format object:

>     {message: {
>          hash: "...",
>          ...
>         }
>     }

In addition to the message hash, the following fields can be used to update the
message:

> `processed`
> 
> > Set this to true to tell the server that the message action has been
> > processed by the message recipient.
> 
> `read`
> 
> > Set this to true to tell the server that the given message has been read by
> > the recipient.

Note that only the recipient can update a message.

If the update was accepted, the API endpoint will return an HTTP response code
of 200 (OK).  If there is no message with the given hash value, the API
endpoint will return an HTTP response code of 404 (Not Found).  If the HMAC
authentication details are missing or invalid, the API endpoint will return an
HTTP response code of 403 (Forbidden).  If some required fields are missing,
the API will return a response code of 400 (Bad Request).


### Polling for Changes ###

**`GET api/changes`**

Return a list of everything that has changed since the last time we polled for
changes.  This API endpoint must use HMAC authentication.  The following
query-string parameter are supported:

> `my_global_id` _(required)_
> 
> > The current user's global ID.
> 
> `anchor` _(optional)_
> 
> > A string used to identify the current state of the system.

> _**Note**: the current user must have an existing profile for this API
> endpoint to work._

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing the following JSON-format object:

>     {changes: [...],
>      next_anchor: "..."
>     }

If the `anchor` parameter was not supplied, only the `next_anchor` field will
be present.  This will hold the anchor value that represents the current state
of the system, and should be used for subsequent polling requests.

If the `anchor` parameter was supplied, the `changes` array will hold a copy of
all the records which have been added or updated since the given anchor value
was calculated.  Each item in the `changes` array will be an object with the
following fields:

>     {type: "...",
>      data: {...}
>     }

The `type` field indicates the type of record being returned, while the `data`
field contains a copy of the new or updated record.  The following `type`
values are currently supported:

>     profile
>     picture
>     conversation
>     message

Note that a message may be updated more than once; if the status of a message
changes, it will be included in the poll results again.  The client should
compare the message hash to see if the message has already been received, and
if so just update the existing message's status.  Note that only the `status`
and `error` fields will ever be updated for a message.

If a record has been deleted, the `data` object will include fields to identify
the record, and an extra field named `deleted` which will be set to true.

The returned `next_anchor` value should be used to make a subsequent call to
the `GET api/changes` endpoint to retrieve any new or updated records since the
last time this endpoint was called.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If there is no user
profile for either of the supplied global ID values, the API endpoint will
return an HTTP response code of 404 (Not Found).


<center>
    <h1><pre>mmServer</pre></h1>
</center>

`mmServer` is a Django project that implements the server-side logic for the
MessageMe system.  The `mmServer` system provides a simple API that allows for
the following server-side functionality:

 * Creating, updating and retrieving a user's own profile.
<br/><br/>
 * Viewing the publically-visible parts of another user's profile.
<br/><br/>
 * Storing, retrieving and updating profile pictures.
<br/><br/>
 * Keeping track of a user's list of conversations.
<br/><br/>
 * Keeping track of the messages for a given conversation.
<br/><br/>
 * Sending messages.
<br/><br/>
 * Keeping track of each user's account balance.
<br/><br/>
 * Making deposits and withdrawals against the user's MessageMe account.
<br/><br/>
 * Charging users for the messages they send.

In addition to the API, the `mmServer` system provides an **Admin Interface**
which lets suitably authorised people view data and enter manual adjustments
against accounts.

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
> > The name of the profile's owner.
> 
> `name_visible`
> 
> > Is the profile name visible to other users?
> 
> `email`
> 
> > The email address of the profile's owner.
> 
> `address_1`
> 
> > The first line of the profile owner's street address.
> 
> `address_1_visible`
> 
> > Is the first line of the address visible to other users?
> 
> `address_2`
> 
> > The second line of the profile owner's street address.
> 
> `address_2_visible`
> 
> > Is the second line of the address visible to other users?
> 
> `city`
> 
> > The name of the city where the profile's owner is based.
> 
> `city_visible`
> 
> > Is the city visible to other users?
> 
> `state_province_or_region`
> 
> > The name of the state, province or region where the profile's owner is
> > based.
> 
> `state_province_or_region_visible`
> 
> > Is the state, province or region visible to other users?
> 
> `zip_or_postal_code`
> 
> > The ZIP or postal code where the profile's owner is based.
> 
> `zip_or_postal_code_visible`
> 
> > Is the ZIP or postal code visible to other users?
> 
> `country`
> 
> > The name of the country where the profile's owner is based.
> 
> `country_visible`
> 
> > Is the country visible to other users?
> 
> `date_of_birth`
> 
> > The profile owner's date of birth, as a string of the form "YYYY-MM-DD".
> > Note that this is never made public.
> 
> `social_security_number_last_4_digits`
> 
> > The last four digits of the profile owner's social security number.  Note
> > that this is never made public.
> 
> `bio`
> 
> > A brief biography of the profile's owner.
> 
> `bio_visible`
> 
> > Is the bio visible to other users?
> 
> `picture_id`
> 
> > The ID of the profile picture uploaded by the user, if any.
> 
> `picture_id_visible`
> 
> >  Is the profile picture visible to other users?

Note that the profile object returned by the API will only contain the
publically-visible portions of the profile if the user is attempting to view
another user's profile.

## User Accounts ##

Each message sent through the MessageMe system has two different types of
charges associated with it: a **system charge** which is the amount which must
be paid to MessageMe for the message to be sent, and a **recipient charge**
which is the amount which must be paid to the message recipient for them to
accept the message.  For a given message, the system and recipient charges can
either be zero or a positive amount -- some messages may incur both a system
and a recipient charge, some may incur just a system charge, some may incur
just a recipient charge, and some messages may be free.  Charges are always
measured in drops (millions of an XRP).

As messages are sent, these charges are incurred by the message sender.  The
charges are then paid to either the message recipient, or to MessageMe itself.
To keep track of these payments, each user has their own **account** within the
MessageMe system.  Each account has a **current balance**, and a list of
**transactions** recording the various deposits and withdrawals made against
that account.  The user is able to **deposit** funds into their MessageMe
account by transferring funds from their Ripple account to MessageMe, and
MessageMe will automatically **withdraw** funds as required to cover the
charges incurred while sending the user's messages.  If the user attempts to
send a message when insufficient funds are available in their account, the
message will fail with an `Insufficent Funds` error.

Recipient charges are paid to the message recipient, in the form of a deposit
into their account.  Similarly, MessageMe itself has its own internal account,
and all system charges are deposited into that account.  Another internal
account, the **Ripple Holding Account**, is used to keep track of deposits made
to MessageMe via the Ripple network -- this account is needed because the
accounts within MessageMe follow standard double-entry bookeeping rules where
every transaction involves both a credit and a debit.

Funds can also be withdrawn from the user's MessageMe account and sent back to
the user's Ripple account.  This can be done to retrieve funds given to
MessageMe, or to take out funds which have been received in the form of
recipient charges.

Internally, each account has the following information associated with it:

> `account_id`
> 
> > A unique ID number for this account.
> 
> `type`
> 
> > A string identifying the type of account.  The following account types are
> > supported:
> > 
> > > `USER`
> > > 
> > > > A user account.
> > > 
> > > `MESSAGEME`
> > > 
> > > > The MessageMe account.
> > >
> > > `RIPPLE_HOLDING`
> > > 
> > > > The Ripple holding account.
> 
> `global_id`
> 
> > For a user account, this is the user's global ID.  Note that this is left
> > blank for non-user accounts.
> 
> `balance`
> 
> > The account's current balance.  This is updated by the server whenever a
> > new transaction is created for this account.

Each account also has a list of transactions associated with it.  For each
transaction, the following information will be stored:

> `transaction_id`
> 
> > A unique ID number associated with this transaction.
> 
> `timestamp`
> 
> > The date and time when this transaction was made, in UTC.
> 
> `type`
> 
> > A string indicating the type of transaction.  The following type values are
> > currently supported:
> > 
> > > `DEPOSIT`
> > > 
> > > > A deposit received from the user to "top up" their MessageMe account.
> > > > This corresponds to funds being transferred from the user's Ripple
> > > > account to the MessageMe Ripple Holding account.
> > > 
> > > `WITHDRAWAL`
> > > 
> > > > A withdrawal of funds from the user's account.  This corresponds to
> > > > funds being transferred from the MessageMe Ripple Holding account to
> > > > the user's Ripple account.
> > > 
> > > `SYSTEM_CHARGE`
> > > 
> > > > A system charge, debiting the user's account and crediting the
> > > > MessageMe account.
> > > 
> > > `RECIPIENT_CHARGE`
> > > 
> > > > A recipient charge, debiting the user's account and crediting the
> > > > MessageMe account of the recipient.
> > > 
> > > `ADJUSTMENT`
> > > 
> > > > A manual adjustment.  These are created by a system administrator to
> > > > correct mistakes.
> 
> `amount`
> 
> > The amount of the transaction, in drops.
> 
> `debit_account`
> 
> > The account which was debited by this transaction.
> 
> `credit_account`
> 
> > The account which was credited by this transaction.
> 
> `message_hash`
> 
> > If this transaction was associated with a message, this is the hash value
> > uniquely identifying the message.  This will be blank for transactions that
> > are not associated with messages.
> 
> `description`
> 
> > A textual description of this transaction.  This will generally be left
> > blank, except for manual adjustments where this is used to explain why the
> > adjustment was made.


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
> `last_message_1`
> 
> > The text of the last message sent for this conversation, as shown to the
> > first user.  If there are no messages in this conversation, this will be
> > set to a `null` value.
> 
> `last_message_2`
> 
> > The text of the last message sent for this conversation, as shown to the
> > second user.  If there are no messages in this conversation, this will be
> > set to a `null` value.
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
>     last_message_1 => last_message
>     last_timestamp => last_timestamp
>     num_unread_1   => num_unread

Conversely, if the current user's global ID matches `global_id_2`, then the API
will return the following set of fields back to the caller:

>     global_id_2    => my_global_id
>     global_id_1    => their_global_id
>     hidden_2       => hidden
>     last_message_2 => last_message
>     last_timestamp => last_timestamp
>     num_unread_2   => num_unread

This ensures that each user sees the conversation from their particular point
of view, while still having a single global conversation record for both users.


## Messages ##

A **message** is the unit of communication between users.  Messages can be
freeform text, or they can include **actions** that need to be performed.
Note that there are two versions of the text for each message: the version to
show to the sender of the message, and the version to show to the message
recipient.  For freeform text messages, both versions will be identical, but
for messages with actions the text of the message will describe the action from
both the sender's and the recipient's point of view.

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
> `sender_text`
> 
> > The text of the message, as shown to the sender of the message.
> 
> `recipient_text`
> 
> > The text of the message, as shown to the recipient of the message.
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
> > > 
> > > `DECLINE_REQUEST_XRP`
> > > 
> > > > Decline a request to send some XRP to the other user.
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
> > * For the `DECLINE_REQUEST_XRP` action:
> > 
> > > > `amount`
> > > > 
> > > > > The amount that the user declined to send, as an integer number of
> > > > > drops.
> > 
> > If the message does not have any action parameters, the `action_params`
> > field will be set to a `null` value.
> 
> `action_processed`
> 
> > Has this action been processed by the recipient?
> 
> `system_charge`
> 
> > The amount to be paid to MessageMe itself for sending this message, as an
> > integer number of drops.
> 
> `recipient_charge`
> 
> > The amount to be paid to the recipient of the message for sending this
> > message, as an integer number of drops.
> 
> `status`
> 
> > The message's current status.  This can be one of the following strings:
> > 
> > > `PENDING`
> > > 
> > > > The message has been accepted, but is waiting for an associated Ripple
> > > > transaction to be confirmed before the message can go through.  Note
> > > > that this status only applies to messages which have a Ripple
> > > > transaction associated with them; ordinary messages will immediately be
> > > > given a status of `SENT` as they go through right away.
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

The following query-string parameters can be supplied if you wish:

> `max_width`
> 
> > The maximum width of the image, in pixels.
> 
> `max_height`
> 
> > The maximum height of the image, in pixels.

If one or both of these parameters are supplied, the image will be scaled to
match the supplied maximum width or height, while maintaining the aspect ratio
of the original image.  If neither parameter is supplied, the image will be
returned unscaled.

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
> 
> `num_msgs` _(optional)_
> 
> > The maximum number of messages to return.  If this is not supplied, we will
> > return a maximum of 20 messages.  Setting this to -1 will cause all
> > messages to be returned.
> 
> `from_msg` _(optional)_
> 
> > If this is supplied, we return the `num_msgs` messages before the message
> > with the given hash value.  If this is not supplied, we return the most
> > recent `num_msgs` messages.

> _**Note**: the current user must have an existing profile for this API
> endpoint to work._

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing the following JSON-format data:

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
>           system_charge: 5,
>           recipient_charge: 0,
>           status: "...",
>           error: "..."},
>          ...
>      ],
>      has_more: true
>     }

Each entry in the `messages` list is an object with the details of the message,
as described in the Messages section, above.  The message text will be selected
based on whether the current user is the sender or the receipient of the
message.  The `error` field will only be present if the message failed to be
sent.

The `has_more` field will be set to `true` if there are more messages for this
query.  Otherwise, it will be set to `false`.

If the `their_global_id` parameter was supplied, only messages between the two
users will be returned.  Otherwise, all messages sent to or received by the
current user will be returned.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If there is no user
profile for either of the supplied global ID values, the API endpoint will
return an HTTP response code of 404 (Not Found).

**`GET api/message`**

Retrieve a single message.  This API endpoint must use HMAC authentication.
The following query-string parameters are required:

> `my_global_id` _(required)_
> 
> > The current user's global ID.
> 
> `message_hash` _(required)_
> 
> > The hash uniquely identifying the desired message.
> 
> _**Note**: the current user must have an existing profile for this API
> endpoint to work._

Upon completion, this API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing the following JSON-format data:

>     {message: {
>          hash: "...",
>          timestamp: 1420173182,
>          sender_global_id: "...",
>          recipient_global_id: "...",
>          sender_account_id: "...",
>          recipient_account_id: "...",
>          text: "...",
>          action: "...",
>          action_params: "...",
>          system_charge: 5,
>          recipient_charge: 0,
>          status: "...",
>          error: "..."}
>     }

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden).  If there is no message
with the given hash value, the API endpoint will return an HTTP response code
of 404 (Not Found).  If the current user is not the sender or recipient of this
message, the API endpoint will return an HTTP response code of 403 (Forbidden).

**`POST api/message`**

Attempt to send a message.  This API endpoint must use HMAC authentication.
The body of the request should be a string containing the following JSON-format
object:

>     {message: {
>           sender_global_id: "...",
>           recipient_global_id: "...",
>           sender_account_id: "...",
>           recipient_account_id: "...",
>           sender_text: "...",
>           recipient_text: "...",
>           action: "...",
>           action_params: "...",
>           system_charge: 5,
>           recipient_charge: 0}
>     }

**_Notes_**:
 
> * The sending user must have an existing profile for this API endpoint to
>   work.
> <br/><br/>
> * Two versions of the message text must be supplied: one to be seen by the
>   message sender, and the other to be seen by the message recipient.  For
>   freeform messages, both versions should be identical, while for a message
>   that has an action associated with it, the message text should be
>   personalised to describe the action from that user's point of view.
> <br/><br/>
> * The `action` and `action_params` fields are only required if the message
>   has an action associated with it.
> <br/></br>
> * The `system_charge` and `recipient_charge` fields should be filled in with
>   the appropriate charges for this message.  Before the message is delivered,
>   these charges will be deducted from the sender's account.

If the message was accepted, the API endpoint will return an HTTP response code
of 202 (Accepted).  For straightforward messages, the message is accepted
immediately, but for messages which involve a payment-related action, the
message will be pending until that action is completed.

If there was something wrong with the request (for example, if the destination
account didn't exist, or a required field was missing), the API will return a
response code of 400 (Bad Request), and the body of the response will be a
string describing why the request failed.  If the HMAC authentication details
are missing or invalid, the API endpoint will return an HTTP response code of
403 (Forbidden).  If the message could not be sent because the sender has
insufficient funds in their account, the API endpoint will return an HTTP
response code of 402 (Payment Required).

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


### Endpoints for the Account Resource ###

**`GET api/account`**

Returns the user's current MessageMe account details.  This API endpoint must
use HMAC authentication.  The following query-string parameters are supported:

> `global_id` _(required)_
> 
> > The current user's global ID.
> 
> `return` _(required)_
> 
> > The type of information to return.  The following values are currently
> > supported:
> > 
> > > `balance`
> > > 
> > > > The user's current account balance.
> > > 
> > > `transactions`
> > > 
> > > > A list of individual transactions.
> > > 
> > > `totals`
> > > 
> > > > The transaction totals -- that is, the sum of all transactions grouped
> > > > according to the value of the `group` parameter.
> 
> `group` _(optional)_
> 
> > If we are calculating the transaction totals, how to group the
> > transactions before totalling them.  The following values are currently
> > supported:
> > 
> > > `type`
> > > 
> > > > Calculate the totals by transaction type.
> > >
> > > `conversation`
> > > 
> > > > Calculate the totals by conversation.
> > > 
> > > `date`
> > > 
> > > > Calculate the totals by date.
> > 
> > If no grouping value is supplied and we are calculating transaction totals,
> > the transaction totals will be calculated by transaction type.
> 
> `type` _(optional)_
> 
> > Only include transactions of the given type in the results.  The following
> > type values are currently supported:
> > 
> > > `charges_paid`  
> > > `charges_received`  
> > > `deposits`  
> > > `withdrawals`  
> > > `adjustments_paid`  
> > > `adjustments_received`
> 
> `conversation` _(optional)_
> 
> > Only include transactions which involved the given conversation in the
> > results.  If this parameter is supplied, it should be the global ID of the
> > other person the conversation was with.
> 
> `date` _(optional)_
> 
> > Only include transactions on the given date.  If this parameter is
> > supplied, it should be a string of the form `YYYY-MM-DD`.  The API endpoint
> > will only include transactions in the results which were created between
> > 12:00 AM and 11:59 PM on that date, using the specified `tz_offset` value
> > to adjust for the end user's timezone.  If `tz_offset` is not supplied, the
> > date will be considered to be in UTC.
> 
> `tz_offset` _(optional)_
> 
> > The difference between UTC and the the user's local time, in minutes.  If
> > this parameter is not supplied, all dates will be considered to be in UTC.

> `tpp` _(optional)_
> 
> > If we are returning a list of individual transactions, this should be the
> > maximum number of transactions to return per request.  If this is not
> > specified, a maximum of 20 transactions will be returned in one go.
> 
> `page` _(optional)_
> 
> > If we are returning a list of individual transactions, this should be the
> > page number of the transactions to return.  Transactions are turned in
> > reverse date order (that is, the most recent transaction will be returned
> > first), and the first page of transactions has a page number of zero.  To
> > obtain more transactions, re-issue the API call with an increasing `page`
> > value until no more transactions are returned.
> > 
> > If the `page` parameter is not supplied, a default value of zero will be
> > used.  This has the effect of returning the first page (ie, the most
> > recent) transactions.

Upon completion, the API endpoint will return an HTTP response code of 200
(OK) if the request was successful.  The body of the response will be a string
containing a JSON-formatted object; the contents of this object will vary
depending on the value of the `return` parameter, as described below:

> **`return=balance`**
> 
> > In this case, the returned object will look like the following:
> > 
> > >     {balance: 999}
> > 
> > where `balance` is the user's current account balance, in drops.
> 
> **`return=transactions`**
> 
> > In this case, the returned object will look like the following:
> > 
> > >     {transactions: [...]}
> > 
> > Each entry in the `transactions` array will be an object with the following
> > fields:
> > 
> > > `transaction_id`
> > > 
> > > > A unique ID number associated with this transaction.
> > > 
> > > `timestamp`
> > > 
> > > > The date and time when this transaction was made, as a unix timestamp
> > > > value in UTC.
> > > 
> > > `type`
> > > 
> > > > A string indicating the type of transaction.  The following type values
> > > > are currently supported:
> > > > 
> > > > > `DEPOSIT`
> > > > > 
> > > > > > A deposit received from the user to "top up" their MessageMe
> > > > > > account.  This corresponds to funds being transferred from the
> > > > > > user's Ripple account to the MessageMe Ripple Holding account.
> > > > > 
> > > > > `WITHDRAWAL`
> > > > > 
> > > > > > A withdrawal of funds from the user's account.  This corresponds to
> > > > > > funds being transferred from the MessageMe Ripple Holding account
> > > > > > to the user's Ripple account.
> > > > > 
> > > > > `SYSTEM_CHARGE_PAID`
> > > > > 
> > > > > > A system charge, debiting the user's account and crediting the
> > > > > > MessageMe account.
> > > > > 
> > > > > `RECIPIENT_CHARGE_PAID`
> > > > > 
> > > > > > A recipient charge, debiting the user's account and crediting the
> > > > > > MessageMe account of the recipient.
> > > > > 
> > > > > `RECIPIENT_CHARGE_RECEIVED`
> > > > > 
> > > > > > A recipient charge, debiting the other user's MessageMe account and
> > > > > > crediting the current user's MessageMe account.
> > > > > 
> > > > > `ADJUSTMENT_PAID`
> > > > > 
> > > > > > A manual adjustment debited from the user's MessageMe account.
> > > > > > These are created by a system administrator to correct mistakes.
> > > > > 
> > > > > `ADJUSTMENT_RECEIVED`
> > > > > 
> > > > > > A manual adjustment credited to the user's MessageMe account.
> > > > > > These are created by a system administrator to correct mistakes.
> > > 
> > > `amount`
> > > 
> > > > The amount of the transaction, in drops.
> > > 
> > > `other_account_type`
> > > 
> > > > The type of the other account involved in this transaction.  One of:
> > > > 
> > > > > `USER`
> > > > > 
> > > > > > A user account.
> > > > > 
> > > > > `MESSAGEME`
> > > > >
> > > > > > The MessageMe account.
> > > > > 
> > > > > `RIPPLE_HOLDING`
> > > > > 
> > > > > > The Ripple holding account.
> > > 
> > > `other_account_global_id`
> > > 
> > > > For a user account, this will be the global ID of the owner of the other
> > > > account involved in this transaction.  Note that this is only supplied
> > > > where the `other_account_type` is `USER`.
> > > 
> > > `message_hash`
> > > 
> > > > If this transaction was associated with a message, this is the hash value
> > > > uniquely identifying the message.  This field will not be present for
> > > > transactions that are not associated with messages.
> > 
> > The transactions will be returned in descending timestamp order -- that is,
> > the most recent transaction will be returned first.
> > 
> > Note that only those transactions with a `status` value of "SUCCESS" will
> > be included in this list. Pending and failed transactions will never be
> > included.
> 
> **`return=totals`**
> 
> > In this case, the returned object will hold the calculated transaction
> > totals.  The exact set of fields in the returned object will vary depending
> > on the value of the `group` parameter:
> > 
> > > **`group=type`**
> > > 
> > > > In this case, the returned object will look like the following:
> > > > 
> > > > >     {types: [...]}
> > > > 
> > > > Each entry in the `types` list will be an object with the following
> > > > fields:
> > > > 
> > > > > `type`
> > > > > 
> > > > > > The type of transaction that this entry is for.  The following type
> > > > > > values are currently supported:
> > > > > > 
> > > > > > > `charges_paid`  
> > > > > > > `charges_received`  
> > > > > > > `deposits`  
> > > > > > > `withdrawals`  
> > > > > > > `adjustments_paid`  
> > > > > > > `adjustments_received`
> > > > > 
> > > > > `total`
> > > > > 
> > > > > > The total value of all the transactions of this type, in drops.
> > > 
> > > **`group=conversation`**
> > > 
> > > > In this case, the returned object will look like the following:
> > > > 
> > > > >     {conversations: [...]}
> > > > 
> > > > Each entry in the `conversations` list will be an object with the
> > > > following fields:
> > > > 
> > > > > `global_id`
> > > > > 
> > > > > > The global ID of the person this conversation was with.
> > > > > 
> > > > > `name`
> > > > > 
> > > > > > The public name for this user, if available.
> > > > > 
> > > > > `total`
> > > > > 
> > > > > > The total value of the matching transactions for this conversation,
> > > > > > in drops.
> > > > 
> > > >  The conversations will be sorted alphabetically by name.  If the
> > > >  user's name is not available, the global ID will be used instead.
> > > 
> > > **`group=date`**
> > > 
> > > > In this case, the returned object will look like the following:
> > > > 
> > > > > {dates: [...]}
> > > > 
> > > > Each entry in the 'dates' list will be an object with the following
> > > > fields:
> > > > 
> > > > > `date`
> > > > > 
> > > > > > The date, as a string in the form `YYYY-MM-DD`.  If a `tz_offset`
> > > > > > value was supplied, this date will be in the user's timezone;
> > > > > > otherwise it will be in UTC.
> > > > > 
> > > > > `total`
> > > > > 
> > > > > > The total value of the matching transactions for this date, in
> > > > > > drops.
> > > > 
> > > > The dates are in inverse order -- that is, the most recent date will be
> > > > first in the list.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden). If some required fields
are missing, the API will return a response code of 400 (Bad Request).  If
there is no user with the given global ID, the API will return a response code
of 404 (Not Found).

> <hr>
> 
> __LEGACY MODE__
> 
> To maintain backward-compatibility with the previous version of the MessageMe
> app, this API endpoint also accepts the following parameter combination to
> return a simple legacy version of the transaction totals:
> 
> > `global_id`
> > 
> > > The currently signed-in user's global ID.
> > 
> > `totals`
> > 
> > > The value `yes`.
> 
> With this combination of parameters, this API endpoint will operate in legacy
> mode.  In this case, the returned JSON object will have the following fields:
> 
> >     {account: {
> >         totals: {
> >             deposits: 999,
> >             withdrawals: 999,
> >             system_charges: 999,
> >             recipient_charges: 999,
> >             adjustments: 999
> >         }
> >      }
> >     }
> 
> The numbers will be the total value of all the transactions of that type,
> measured in drops.  Note that the grouping is simply by transaction type,
> rather than the more sophisticated breakdown supported by the new version of
> this endpoint.
> 
> <hr>

### Endpoints for the Transaction Resource ###

**`POST api/transaction`**

Submit a transaction to the user's MessageMe account.  This API endpoint must
use HMAC authentication.  The body of the request should be a string containing
the following JSON-formatted object:

>     {global_id: "...",
>      ripple_account: "...",
>      type: "...",
>      amount: 100,
>      description: "..."
>     }

The JSON-format object should include the following fields:

> `global_id` _(required)_
> 
> > The current user's global ID.
> 
> `ripple_account` _(required)_
> 
> > The current user's Ripple account address.
> 
> `type` _(required)_
> 
> > A string indicating the type of transactions to submit.  The following
> > transaction types are currently supported:
> > 
> > > `DEPOSIT`  
> > > `WITHDRAWAL`  
> 
> `amount` _(required)_
> 
> > The desired amount, in drops.
> 
> `description` _(optional)_
> 
> > An optional description to associate with this transaction.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden). If some required fields
are missing, the API will return a response code of 400 (Bad Request).

If the request was valid, the API endpoint will return an HTTP response code of
200 (OK).  In this case, the body of the response will consist of a JSON-format
object describing the results of the request.  If a new transaction was
successfully created, the JSON object will look like the following:

>     {status: "PENDING",
>      transaction_id: 12345}

If the transaction could not be created for some reason, the following JSON
data will be returned:

>     {status: "FAILED",
>      transaction_id: 12345,
>      error: "..."}

In this case, the `error` field will be a string describing why the transaction
failed.

For a manual deposit, the server will attempt to transfer the funds from the
user's Ripple account to the MessageMe Ripple Holding Account.  Once this
Ripple transaction has gone through, the user's MessageMe account will be
credited by the same amount.

For a manual withdrawal, the server will first check to see that the user's
MessageMe account has sufficient funds to cover the withdrawal.  If it does,
the user's MessageMe account will be debited by this amount, and a Ripple
transaction will be initiated transferring the funds from the Ripple Holding
Account back into the user's own Ripple account.  If this transaction fails for
any reason, then the funds will be credited back into the user's MessageMe
account.

Because these processes take time, the associated `DEPOSIT` or `WITHDRAWAL`
transaction will initially be given a status of `PENDING`.  You can then check
the final status of the transaction by polling the `GET api/transaction`
endpoint to see when the transaction becomes finalized.

**`GET api/transaction`**

Return the current status of a single transaction.  The following query-string
parameters are supported:

> `global_id` _(required)_
> 
> > The current user's global ID.
> 
> `transaction_id` _(required)_
> 
> > The ID of the desired transaction.

If the HMAC authentication details are missing or invalid, the API endpoint
will return an HTTP response code of 403 (Forbidden). If some required fields
are missing, the API will return a response code of 400 (Bad Request).  If the
given transaction is missing, the API will return an HTTP response code of 404
(Not Found).  If the given transaction is not associated with the given user's
MessageMe account, the API endpoint will return an HTTP response code of 400
(Bad Request).

If the request was valid, the API endpoint will return an HTTP response code of
200 (OK).  In this case, the body of the response will consist of a JSON-format
object describing the current status of the given transaction.  If the
transaction is still pending, the following data will be returned:

>     {status: "PENDING"}

If the transaction was successful, the following will be returned:

>     {status: "SUCCESS"}

If the transaction failed to go through for some reason, the following JSON
data will be returned:

>     {status: "FAILED",
>      error: "..."}

In this case, the `error` field will be a string describing why the transaction
failed.


### Polling for Changes ###

**`GET api/changes`**

Return a list of everything that has changed since the last time we polled for
changes.  This API endpoint must use HMAC authentication.  The following
query-string parameters are supported:

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


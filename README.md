# `mmServer` #

`mmServer` is a Django project that implements the server-side logic for the
MessageMe system.  The `mmServer` system provides a simple API that allows for
the following server-side functionality:

 * Creating, updating and retrieving a user's own profile.
<br/><br/>
 * Viewing the publically-visible parts of another user's profile.
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
> `picture_url`
> 
> > The URL of the profile picture uploaded by the user.
> 
> `picture_url_visible`
> 
> >  A boolean indicating whether the profile picture is visible to other
> >  users.

Note that the profile object returned by the API will only contain the
publically-visible portions of the profile if the user is attempting to view
another user's profile.


## Authentication ##

To ensure that a user can only update or retrieve the full contents of their
own profile, we use Hash-based Message Authentication (HMAC) based on the
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
    * The URL for the desired API request, excluding the server name.
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


## API Endpoints ##

The following endpoints are currently supported by the `mmServer` API:

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

***More to come...***


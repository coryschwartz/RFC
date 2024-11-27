---
title: Secure Frame (SFrame)
abbrev: SFrame
docname: draft-ietf-sframe-enc-latest
category: std

ipr: trust200902
stream: IETF
area: "Applications and Real-Time"
wg: sframe
keyword: Internet-Draft
v: 3

author:
 -
    ins: E. Omara
    name: Emad Omara
    organization: Apple
    email: eomara@apple.com
 -
    ins: J. Uberti
    name: Justin Uberti
    organization: Google
    email: juberti@google.com
 -
    ins: S. Murillo
    name: Sergio Garcia Murillo
    organization: CoSMo Software
    email: sergio.garcia.murillo@cosmosoftware.io
 -
    ins: R.L. Barnes
    name: Richard L. Barnes
    organization: Cisco
    email: rlb@ipv.sx
    role: editor
 -
    ins: Y. Fablet
    name: Youenn Fablet
    organization: Apple
    email: youenn@apple.com

contributor:
 -
    ins: F. Jacobs
    name: Frederic Jacobs
    organization: Apple
    email: frederic.jacobs@apple.com
 -
    ins: M. Mularczyk
    name: Marta Mularczyk
    organization: Amazon
    email: mulmarta@amazon.com
 -
    ins: S. Nandakumar
    name: Suhas Nandakumar
    organization: Cisco
    email: snandaku@cisco.com
 -
    ins: T. Rigaux
    name: Tomas Rigaux
    organization: Cisco
    email: trigaux@cisco.com
 -
    ins: R. Robert
    name: Raphael Robert
    organization: Phoenix R&D
    email: ietf@raphaelrobert.com

informative:
  TestVectors:
    title: "SFrame Test Vectors"
    refcontent: commit 025d568
    target: https://github.com/sframe-wg/sframe/blob/main/test-vectors/test-vectors.json
    date: 2023-09


--- abstract
<!--[rfced] Please insert any keywords (beyond those that appear in the title) for use on https://www.rfc-editor.org/search. -->
<!--[rfced] Richard, do prefer "R. L. Barnes, Ed." (current) or "R. Barnes, Ed." (as used in other RFCs) in the header of the document? -->
<!--[rfced] May we make the title more descriptive? We note that a web search on "SFrame" returns pages describing different technologies.

Current: Secure Frame (SFrame)

Perhaps: Secure Frame (SFrame): an Encryption and Authentication Mechanism for Media Frames
-->
This document describes the Secure Frame (SFrame) end-to-end encryption and
authentication mechanism for media frames in a multiparty conference call, in
which central media servers (Selective Forwarding Units or SFUs) can access the
media metadata needed to make forwarding decisions without having access to the
actual media.

This mechanism differs from the Secure Real-Time Protocol (SRTP) in that
it is independent of RTP (thus compatible with non-RTP media transport) and can
be applied to whole media frames in order to be more bandwidth efficient.

--- middle


# Introduction

Modern multiparty video call systems use Selective Forwarding Unit (SFU)
servers to efficiently route media streams to call endpoints based on factors such
as available bandwidth, desired video size, codec support, and other factors. An
SFU typically does not need access to the media content of the conference,
which allows the media to be encrypted "end to end" so that it cannot be
decrypted by the SFU. In order for the SFU to work properly, though, it usually
needs to be able to access RTP metadata and RTCP feedback messages, which is not
possible if all RTP/RTCP traffic is end-to-end encrypted.

As such, two layers of encryption and authentication are required:

  1. Hop-by-hop (HBH) encryption of media, metadata, and feedback messages
     between the endpoints and SFU
  2. End-to-end (E2E) encryption (E2EE) of media between the endpoints

The Secure Real-Time Protocol (SRTP) is already widely used for HBH encryption
{{?RFC3711}}. The SRTP "double encryption" scheme defines a way to do E2E
encryption in SRTP {{?RFC8723}}. Unfortunately, this scheme has poor efficiency
and high complexity, and its entanglement with RTP makes it unworkable in
several realistic SFU scenarios.

This document proposes a new E2EE protection scheme known as SFrame,
specifically designed to work in group conference calls with SFUs. SFrame is a
general encryption framing that can be used to protect media payloads, agnostic
of transport.

# Terminology

{::boilerplate bcp14-tagged}

MAC:
: Message Authentication Code

E2EE:
: End-to-End Encryption

HBH:
: Hop-By-Hop

We use "Selective Forwarding Unit (SFU)" and "media stream" in a less formal sense
than in {{?RFC7656}}.  An SFU is a selective switching function for media
payloads, and a media stream a sequence of media payloads, in both cases
regardless of whether those media payloads are transported over RTP or some
other protocol.

<!--[rfced] Section 2. We're having difficulty parsing the following sentence. Would it be clearer to remove "in both cases"?:

Original:
   An SFU is a selective switching
   function for media payloads, and a media stream a sequence of media
   payloads, in both cases regardless of whether those media payloads
   are transported over RTP or some other protocol.

Perhaps:
   An SFU is a selective switching
   function for media payloads, and a media stream is a sequence of media
   payloads, regardless of whether those media payloads
   are transported over RTP or some other protocol.-->

# Goals

SFrame is designed to be a suitable E2EE protection scheme for conference call
media in a broad range of scenarios, as outlined by the following goals:

<!--[rfced] Section 3. May we make the following list entry parallel with other entries, which start with a verb?

Original:
   4.  Independence from the underlying transport, including use in non-
       RTP transports, e.g., WebTransport

Perhaps:
   4.  Provide independence from the underlying transport, by including
       the use in non-RTP transports, e.g., WebTransport-->

1. Provide a secure E2EE mechanism for audio and video in conference calls
   that can be used with arbitrary SFU servers.

2. Decouple media encryption from key management to allow SFrame to be used
   with an arbitrary key management system.

3. Minimize packet expansion to allow successful conferencing in as many
   network conditions as possible.

4. Independence from the underlying transport, including use in non-RTP
   transports, e.g., WebTransport {{?I-D.ietf-webtrans-overview}}.

5. When used with RTP and its associated error-resilience mechanisms, i.e., RTX
   and Forward Error Correction (FEC), require no special handling for RTX and FEC packets.

6. Minimize the changes needed in SFU servers.

7. Minimize the changes needed in endpoints.

8. Work with the most popular audio and video codecs used in conferencing
   scenarios.

# SFrame

This document defines an encryption mechanism that provides effective E2EE,
is simple to implement, has no dependencies on RTP, and minimizes
encryption bandwidth overhead. This section describes how the mechanism
works and includes details of how applications utilize SFrame for media protection
as well as the actual mechanics of E2EE for protecting media.

## Application Context

SFrame is a general encryption framing, intended to be used as an E2EE
layer over an underlying HBH-encrypted transport such as SRTP or QUIC
{{RFC3711}}{{?I-D.ietf-moq-transport}}.

The scale at which SFrame encryption is applied to media determines the overall
amount of overhead that SFrame adds to the media stream as well as the
engineering complexity involved in integrating SFrame into a particular
environment. Two patterns are common: using SFrame to encrypt either whole
media frames (per frame) or individual transport-level media payloads
(per packet).

For example, {{media-stack}} shows a typical media sender stack that takes media
from some source, encodes it into frames, divides those frames into media
packets, and then sends those payloads in SRTP packets. The receiver stack
performs the reverse operations, reassembling frames from SRTP packets and
decoding.  Arrows indicate two different ways that SFrame protection could be
integrated into this media stack: to encrypt whole frames or individual media
packets.

Applying SFrame per frame in this system offers higher efficiency but may
require a more complex integration in environments where depacketization relies
on the content of media packets. Applying SFrame per packet avoids this
complexity at the cost of higher bandwidth consumption.  Some quantitative
discussion of these trade-offs is provided in {{overhead-analysis}}.

As noted above, however, SFrame is a general media encapsulation and can be
applied in other scenarios.  The important thing is that the sender and
receivers of an SFrame-encrypted object agree on that object's semantics.
SFrame does not provide this agreement; it must be arranged by the application.

~~~ aasvg
      +------------------------------------------------------+
      |                                                      |
      |  +--------+      +-------------+      +-----------+  |
 .-.  |  |        |      |             |      |    HBH    |  |
|   | |  | Encode |----->|  Packetize  |----->|  Protect  |----------+
 '+'  |  |        |   ^  |             |  ^   |           |  |       |
 /|\  |  +--------+   |  +-------------+  |   +-----------+  |       |
/ + \ |               |                   |         ^        |       |
 / \  |            SFrame              SFrame       |        |       |
/   \ |            Protect             Protect      |        |       |
Alice |          (per frame)         (per packet)   |        |       |
      |               ^                   ^         |        |       |
      |               |                   |         |        |       |
      +---------------|-------------------|---------|--------+       |
                      |                   |         |                v
                      |                   |         |         +------+-+
                      |      E2E Key      |       HBH Key     | Media  |
                      +---- Management ---+      Management   | Server |
                      |                   |         |         +------+-+
                      |                   |         |                |
      +---------------|-------------------|---------|--------+       |
      |               |                   |         |        |       |
      |               V                   V         |        |       |
 .-.  |            SFrame               SFrame      |        |       |
|   | |           Unprotect            Unprotect    |        |       |
 '+'  |          (per frame)          (per packet)  |        |       |
 /|\  |               |                    |        V        |       |
/ + \ |  +--------+   |  +-------------+   |  +-----------+  |       |
 / \  |  |        |   V  |             |   V  |    HBH    |  |       |
/   \ |  | Decode |<-----| Depacketize |<-----| Unprotect |<---------+
 Bob  |  |        |      |             |      |           |  |
      |  +--------+      +-------------+      +-----------+  |
      |                                                      |
      +------------------------------------------------------+
~~~
{: #media-stack title="Two Options for Integrating SFrame in a Typical Media Stack" }

Like SRTP, SFrame does not define how the keys used for SFrame are exchanged by
the parties in the conference.  Keys for SFrame might be distributed over an
existing E2E-secure channel (see {{sender-keys}}) or derived from an E2E-secure
shared secret (see {{mls}}).  The key management system MUST ensure that each
key used for encrypting media is used by exactly one media sender in order to
avoid reuse of nonces.

## SFrame Ciphertext

An SFrame ciphertext comprises an SFrame header followed by the output of an
Authenticated Encryption with Associated Data (AEAD) encryption of the plaintext {{!RFC5116}}, with the header provided as additional
authenticated data (AAD).

The SFrame header is a variable-length structure described in detail in
{{sframe-header}}.  The structure of the encrypted data and authentication tag
are determined by the AEAD algorithm in use.
<!--[rfced] Would you like to provide a title for the figure given in Section 4.2? -->

~~~ aasvg
   +-+----+-+----+--------------------+--------------------+<-+
   |K|KLEN|C|CLEN|       Key ID       |      Counter       |  |
+->+-+----+-+----+--------------------+--------------------+  |
|  |                                                       |  |
|  |                                                       |  |
|  |                                                       |  |
|  |                                                       |  |
|  |                   Encrypted Data                      |  |
|  |                                                       |  |
|  |                                                       |  |
|  |                                                       |  |
|  |                                                       |  |
+->+-------------------------------------------------------+<-+
|  |                 Authentication Tag                    |  |
|  +-------------------------------------------------------+  |
|                                                             |
|                                                             |
+--- Encrypted Portion               Authenticated Portion ---+
~~~

When SFrame is applied per packet, the payload of each packet will be an SFrame
ciphertext.  When SFrame is applied per frame, the SFrame ciphertext
representing an encrypted frame will span several packets, with the header
appearing in the first packet and the authentication tag in the last packet.
It is the responsibility of the application to reassemble an encrypted frame from
individual packets, accounting for packet loss and reordering as necessary.

## SFrame Header

The SFrame header specifies two values from which encryption parameters are
derived:

* A Key ID (KID) that determines which encryption key should be used
* A counter (CTR) that is used to construct the nonce for the encryption

Applications MUST ensure that each (KID, CTR) combination is used for exactly
one SFrame encryption operation. A typical approach to achieve this guarantee is
outlined in {{header-value-uniqueness}}.

~~~ aasvg
   Config Byte
        |
 .-----' '-----.
|               |
 0 1 2 3 4 5 6 7
+-+-+-+-+-+-+-+-+------------+------------+
|X|  K  |Y|  C  |   KID...   |   CTR...   |
+-+-+-+-+-+-+-+-+------------+------------+
~~~
{: #fig-sframe-header title="SFrame Header"}

The SFrame header has the overall structure shown in {{fig-sframe-header}}.  The
first byte is a "config byte", with the following fields:

Extended Key ID Flag (X, 1 bit):
: Indicates if the K field contains the Key ID or the Key ID length.

Key or Key Length (K, 3 bits):
: If the X flag is set to 0, this field contains the Key ID.  If the X flag is
set to 1, then it contains the length of the Key ID, minus one.

Extended Counter Flag (Y, 1 bit):
: Indicates if the C field contains the counter or the counter length.

Counter or Counter Length (C, 3 bits):
: This field contains the counter (CTR) if the Y flag is set to 0, or the counter
length, minus one, if set to 1.

The Key ID and Counter fields are encoded as compact unsigned integers in
network (big-endian) byte order.  If the value of one of these fields is in the
range 0-7, then the value is carried in the corresponding bits of the config
byte (K or C) and the corresponding flag (X or Y) is set to zero.  Otherwise,
the value MUST be encoded with the minimum number of bytes required and
appended after the config byte, with the Key ID first and Counter second.
The header field (K or C) is set to the number of bytes in the encoded value,
minus one.  The value 000 represents a length of 1, 001 a length of 2, etc.
This allows a 3-bit length field to represent the value lengths 1-8.

The SFrame header can thus take one of the four forms shown in
{{fig-sframe-header-cases}}, depending on which of the X and Y flags are set.

~~~ aasvg
KID < 8, CTR < 8:
+-+-----+-+-----+
|0| KID |0| CTR |
+-+-----+-+-----+

KID < 8, CTR >= 8:
+-+-----+-+-----+------------------------+
|0| KID |1|CLEN |  CTR... (length=CLEN)  |
+-+-----+-+-----+------------------------+

KID >= 8, CTR < 8:
+-+-----+-+-----+------------------------+
|1|KLEN |0| CTR |  KID... (length=KLEN)  |
+-+-----+-+-----+------------------------+

KID >= 8, CTR >= 8:
+-+-----+-+-----+------------------------+------------------------+
|1|KLEN |1|CLEN |  KID... (length=KLEN)  |  CTR... (length=CLEN)  |
+-+-----+-+-----+------------------------+------------------------+
~~~
{: #fig-sframe-header-cases title="Forms of Encoded SFrame Header" }

## Encryption Schema

SFrame encryption uses an AEAD encryption algorithm and hash function defined by
the cipher suite in use (see {{cipher-suites}}).  We will refer to the following
aspects of the AEAD and the hash algorithm below:

* `AEAD.Encrypt` and `AEAD.Decrypt` - The encryption and decryption functions
  for the AEAD.  We follow the convention of RFC 5116 {{!RFC5116}} and consider
  the authentication tag part of the ciphertext produced by `AEAD.Encrypt` (as
  opposed to a separate field as in SRTP {{?RFC3711}}).

* `AEAD.Nk` - The size in bytes of a key for the encryption algorithm

* `AEAD.Nn` - The size in bytes of a nonce for the encryption algorithm

* `AEAD.Nt` - The overhead in bytes of the encryption algorithm (typically the
  size of a "tag" that is added to the plaintext)

* `AEAD.Nka` - For cipher suites using the compound AEAD described in
  {{aes-ctr-with-sha2}}, the size in bytes of a key for the underlying Advanced Encryption Standard Counter Mode (AES-CTR)
  algorithm

* `Hash.Nh` - The size in bytes of the output of the hash function

### Key Selection

Each SFrame encryption or decryption operation is premised on a single secret
`base_key`, which is labeled with an integer KID value signaled in the SFrame
header.

The sender and receivers need to agree on which `base_key` should be used for a given
KID.  Moreover, senders and receivers need to agree on whether a `base_key` will be used
for encryption or decryption only. The process for provisioning `base_key` values and their KID
values is beyond the scope of this specification, but its security properties will
bound the assurances that SFrame provides.  For example, if SFrame is used to
provide E2E security against intermediary media nodes, then SFrame keys need to
be negotiated in a way that does not make them accessible to these intermediaries.

For each known KID value, the client stores the corresponding symmetric key
`base_key`.  For keys that can be used for encryption, the client also stores
the next counter value CTR to be used when encrypting (initially 0).

When encrypting a plaintext, the application specifies which KID is to be used,
and the counter is incremented after successful encryption.  When decrypting,
the `base_key` for decryption is selected from the available keys using the KID
value in the SFrame header.

A given `base_key` MUST NOT be used for encryption by multiple senders.  Such reuse
would result in multiple encrypted frames being generated with the same (key,
nonce) pair, which harms the protections provided by many AEAD algorithms.
Implementations MUST mark each `base_key` as usable for encryption or decryption,
never both.

Note that the set of available keys might change over the lifetime of a
real-time session.  In such cases, the client will need to manage key usage to
avoid media loss due to a key being used to encrypt before all receivers are
able to use it to decrypt.  For example, an application may make decryption-only
keys available immediately, but delay the use of keys for encryption until (a)
all receivers have acknowledged receipt of the new key, or (b) a timeout expires.

### Key Derivation

SFrame encryption and decryption use a key and salt derived from the `base_key`
associated with a KID.  Given a `base_key` value, the key and salt are derived
using HMAC-based Key Derivation Function (HKDF) {{!RFC5869}} as follows:

<!--[rfced] Section 4.4.2. The following line exceeds the 72-character limit. Please let us know how this line can be modified. 

Current:
     sframe_salt = HKDF-Expand(sframe_secret, sframe_salt_label, AEAD.Nn)
-->

~~~ pseudocode
def derive_key_salt(KID, base_key):
  sframe_secret = HKDF-Extract("", base_key)

  sframe_key_label = "SFrame 1.0 Secret key " + KID + cipher_suite
  sframe_key = HKDF-Expand(sframe_secret, sframe_key_label, AEAD.Nk)

  sframe_salt_label = "SFrame 1.0 Secret salt " + KID + cipher_suite
  sframe_salt = HKDF-Expand(sframe_secret, sframe_salt_label, AEAD.Nn)

  return sframe_key, sframe_salt
~~~

In the derivation of `sframe_secret`:

* The `+` operator represents concatenation of byte strings.

* The KID value is encoded as an 8-byte big-endian integer, not the compressed
  form used in the SFrame header.

* The `cipher_suite` value is a 2-byte big-endian integer representing the
  cipher suite in use (see {{sframe-cipher-suites}}).

The hash function used for HKDF is determined by the cipher suite in use.

### Encryption
<!--[rfced] Section 4.4.3. In the following sentence, is the nonce encoded or is the counter encoded?

Current:
   The key for the encryption is the sframe_key and the
   nonce is formed by XORing the sframe_salt with the current counter,
   encoded as a big-endian integer of length AEAD.Nn.

Perhaps:
   The key for the encryption is the sframe_key, and the
   nonce is formed by XORing the sframe_salt with the current counter
   and encoding it as a big-endian integer of length AEAD.Nn.
-->
SFrame encryption uses the AEAD encryption algorithm for the cipher suite in use.
The key for the encryption is the `sframe_key` and the nonce is formed by XORing
the `sframe_salt` with the current counter, encoded as a big-endian integer of
length `AEAD.Nn`.

The encryptor forms an SFrame header using the CTR and KID values provided.
The encoded header is provided as AAD to the AEAD encryption operation, together
with application-provided metadata about the encrypted media (see {{metadata}}).

~~~ pseudocode
def encrypt(CTR, KID, metadata, plaintext):
  sframe_key, sframe_salt = key_store[KID]

  # encode_big_endian(x, n) produces an n-byte string encoding the
  # integer x in big-endian byte order.
  ctr = encode_big_endian(CTR, AEAD.Nn)
  nonce = xor(sframe_salt, CTR)

  # encode_sframe_header produces a byte string encoding the
  # provided KID and CTR values into an SFrame header.
  header = encode_sframe_header(CTR, KID)
  aad = header + metadata

  ciphertext = AEAD.Encrypt(sframe_key, nonce, aad, plaintext)
  return header + ciphertext
~~~

For example, the metadata input to encryption allows for frame metadata to be
authenticated when SFrame is applied per frame.  After encoding the frame and
before packetizing it, the necessary media metadata will be moved out of the
encoded frame buffer to be sent in some channel visible to the SFU (e.g., an
RTP header extension).

~~~ aasvg
                                  +---------------+
                                  |               |
                                  |               |
                                  |   plaintext   |
                                  |               |
                                  |               |
                                  +-------+-------+
                                          |
        .- +-----+                        |
       |   |     +--+--> sframe_key ----->| Key
Header |   | KID |  |                     |
       |   |     |  +--> sframe_salt --+  |
    +--+   +-----+                     |  |
    |  |   |     +---------------------+->| Nonce
    |  |   | CTR |                        |
    |  |   |     |                        |
    |   '- +-----+                        |
    |                                     |
    |          +----------------+         |
    |          |    metadata    |         |
    |          +-------+--------+         |
    |                  |                  |
    +------------------+----------------->| AAD
    |                                     |
    |                                AEAD.Encrypt
    |                                     |
    |               SFrame Ciphertext     |
    |               +---------------+     |
    +-------------->| SFrame Header |     |
                    +---------------+     |
                    |               |     |
                    |               |<----+
                    |   ciphertext  |
                    |               |
                    |               |
                    +---------------+
~~~
{: title="Encrypting an SFrame Ciphertext" }

### Decryption

Before decrypting, a receiver needs to assemble a full SFrame ciphertext. When
an SFrame ciphertext is fragmented into multiple parts for transport (e.g.,
a whole encrypted frame sent in multiple SRTP packets), the receiving client
collects all the fragments of the ciphertext, using appropriate sequencing
and start/end markers in the transport. Once all of the required fragments are
available, the client reassembles them into the SFrame ciphertext, then it passes
the ciphertext to SFrame for decryption.

The KID field in the SFrame header is used to find the right key and salt for
the encrypted frame, and the CTR field is used to construct the nonce. The SFrame
decryption procedure is as follows:

~~~ pseudocode
def decrypt(metadata, sframe_ciphertext):
  KID, CTR, header, ciphertext = parse_ciphertext(sframe_ciphertext)

  sframe_key, sframe_salt = key_store[KID]

  ctr = encode_big_endian(CTR, AEAD.Nn)
  nonce = xor(sframe_salt, ctr)
  aad = header + metadata

  return AEAD.Decrypt(sframe_key, nonce, aad, ciphertext)
~~~

If a ciphertext fails to decrypt because there is no key available for the KID
in the SFrame header, the client MAY buffer the ciphertext and retry decryption
once a key with that KID is received.  If a ciphertext fails to decrypt for any
other reason, the client MUST discard the ciphertext. Invalid ciphertexts SHOULD be
discarded in a way that is indistinguishable (to an external observer) from having
processed a valid ciphertext.  In other words, the SFrame decrypt operation
should be constant time, regardless of whether decryption succeeds or fails.

~~~ aasvg
                    SFrame Ciphertext
                    +---------------+
    +---------------| SFrame Header |
    |               +---------------+
    |               |               |
    |               |               |-----+
    |               |   ciphertext  |     |
    |               |               |     |
    |               |               |     |
    |               +---------------+     |
    |                                     |
    |   .- +-----+                        |
    |  |   |     +--+--> sframe_key ----->| Key
    |  |   | KID |  |                     |
    |  |   |     |  +--> sframe_salt --+  |
    +->+   +-----+                     |  |
    |  |   |     +---------------------+->| Nonce
    |  |   | CTR |                        |
    |  |   |     |                        |
    |   '- +-----+                        |
    |                                     |
    |          +----------------+         |
    |          |    metadata    |         |
    |          +-------+--------+         |
    |                  |                  |
    +------------------+----------------->| AAD
                                          |
                                     AEAD.Decrypt
                                          |
                                          V
                                  +---------------+
                                  |               |
                                  |               |
                                  |   plaintext   |
                                  |               |
                                  |               |
                                  +---------------+
~~~
{: title="Decrypting an SFrame Ciphertext" }

## Cipher Suites

Each SFrame session uses a single cipher suite that specifies the following
primitives:

* A hash function used for key derivation

* An AEAD encryption algorithm [RFC5116] used for frame encryption, optionally
  with a truncated authentication tag

This document defines the following cipher suites, with the constants defined in
{{encryption-schema}}:

| Name                          | Nh | Nka | Nk | Nn | Nt |
|:------------------------------|:---|:----|:---|:---|:---|
| `AES_128_CTR_HMAC_SHA256_80`  | 32 | 16  | 48 | 12 | 10 |
| `AES_128_CTR_HMAC_SHA256_64`  | 32 | 16  | 48 | 12 |  8 |
| `AES_128_CTR_HMAC_SHA256_32`  | 32 | 16  | 48 | 12 |  4 |
| `AES_128_GCM_SHA256_128`      | 32 | n/a | 16 | 12 | 16 |
| `AES_256_GCM_SHA512_128`      | 64 | n/a | 32 | 12 | 16 |
{: #cipher-suite-constants title="SFrame Cipher Suite Constants" }

Numeric identifiers for these cipher suites are defined in the IANA registry
created in {{sframe-cipher-suites}}.

<!--[rfced] Section 4.5. We have updated the following text to use numerals. Please let us know if any updates are necessary.

Original:
   ... "_128" indicates a hundred-twenty-eight-bit tag,
   "_80" indicates an eighty-bit tag, "_64" indicates a sixty-four-bit
   tag and "_32" indicates a thirty-two-bit tag.

   ... a session might use a cipher suite
   with eighty-bit tags for video frames and another cipher suite with
   thirty-two-bit tags for audio frames.

Current:
   ... "_128" indicates a 128-bit tag,
   "_80" indicates an 80-bit tag, "_64" indicates a 64-bit
   tag, and "_32" indicates a 32-bit tag.

   ... a session might use a cipher suite
   with 80-bit tags for video frames and another cipher suite with
   32-bit tags for audio frames.-->

In the suite names, the length of the authentication tag is indicated by
the last value: "\_128" indicates a 128-bit tag, "\_80" indicates
an 80-bit tag, "\_64" indicates a 64-bit tag, and "\_32" indicates a
32-bit tag.

In a session that uses multiple media streams, different cipher suites might be
configured for different media streams.  For example, in order to conserve
bandwidth, a session might use a cipher suite with 80-bit tags for video frames
and another cipher suite with 32-bit tags for audio frames.

### AES-CTR with SHA2

In order to allow very short tag sizes, we define a synthetic AEAD function
using the authenticated counter mode of AES together with HMAC for
authentication.  We use an encrypt-then-MAC approach, as in SRTP {{?RFC3711}}.

Before encryption or decryption, encryption and authentication subkeys are
derived from the single AEAD key.  The overall length of the AEAD key is `Nka +
Nh`, where `Nka` represents the key size for the AES block cipher in use and `Nh`
represents the output size of the hash function  (as in {{cipher-suite-constants}}).
The encryption subkey comprises the first `Nka` bytes and the authentication
subkey comprises the remaining `Nh` bytes.

~~~ pseudocode
def derive_subkeys(sframe_key):
  # The encryption key comprises the first Nka bytes
  enc_key = sframe_key[..Nka]

  # The authentication key comprises Nh remaining bytes
  auth_key = sframe_key[Nka..]

  return enc_key, auth_key
~~~

The AEAD encryption and decryption functions are then composed of individual
calls to the CTR encrypt function and HMAC.  The resulting MAC value is truncated
to a number of bytes `Nt` fixed by the cipher suite.

~~~ pseudocode
def truncate(tag, n):
  # Take the first `n` bytes of `tag`
  return tag[..n]

def compute_tag(auth_key, nonce, aad, ct):
  aad_len = encode_big_endian(len(aad), 8)
  ct_len = encode_big_endian(len(ct), 8)
  tag_len = encode_big_endian(Nt, 8)
  auth_data = aad_len + ct_len + tag_len + nonce + aad + ct
  tag = HMAC(auth_key, auth_data)
  return truncate(tag, Nt)

def AEAD.Encrypt(key, nonce, aad, pt):
  enc_key, auth_key = derive_subkeys(key)
  initial_counter = nonce + 0x00000000 # append four zero bytes
  ct = AES-CTR.Encrypt(enc_key, initial_counter, pt)
  tag = compute_tag(auth_key, nonce, aad, ct)
  return ct + tag

def AEAD.Decrypt(key, nonce, aad, ct):
  inner_ct, tag = split_ct(ct, tag_len)

  enc_key, auth_key = derive_subkeys(key)
  candidate_tag = compute_tag(auth_key, nonce, aad, inner_ct)
  if !constant_time_equal(tag, candidate_tag):
    raise Exception("Authentication Failure")

  initial_counter = nonce + 0x00000000 # append four zero bytes
  return AES-CTR.Decrypt(enc_key, initial_counter, inner_ct)
~~~

# Key Management

SFrame must be integrated with an E2E key management framework to exchange and
rotate the keys used for SFrame encryption. The key management
framework provides the following functions:

* Provisioning KID / `base_key` mappings to participating clients
* Updating the above data as clients join or leave

It is the responsibility of the application to provide the key management
framework, as described in {{key-management-framework}}.

## Sender Keys

If the participants in a call have a preexisting E2E-secure channel, they can
use it to distribute SFrame keys.  Each client participating in a call generates
a fresh `base_key` value that it will use to encrypt media. The client then uses
the E2E-secure channel to send their encryption key to the other participants.

In this scheme, it is assumed that receivers have a signal outside of SFrame for
which client has sent a given frame (e.g., an RTP synchronization source (SSRC)).  SFrame KID
values are then used to distinguish between versions of the sender's `base_key`.

Key IDs in this scheme have two parts: a "key generation" and a "ratchet step".
Both are unsigned integers that begin at zero.  The "key generation" increments
each time the sender distributes a new key to receivers.  The "ratchet step" is
incremented each time the sender ratchets their key forward for forward secrecy:

~~~ pseudocode
base_key[i+1] = HKDF-Expand(
                  HKDF-Extract("", base_key[i]),
                  "SFrame 1.0 Ratchet", CipherSuite.Nh)
~~~

For compactness, we do not send the whole ratchet step.  Instead, we send only
its low-order `R` bits, where `R` is a value set by the application.  Different
senders may use different values of `R`, but each receiver of a given sender
needs to know what value of `R` is used by the sender so that they can recognize
when they need to ratchet (vs. expecting a new key).  `R` effectively defines a
reordering window, since no more than 2<sup>`R`</sup> ratchet steps can be
active at a given time.  The key generation is sent in the remaining `64 - R`
bits of the Key ID.

~~~ pseudocode
KID = (key_generation << R) + (ratchet_step % (1 << R))
~~~

~~~ aasvg
     64-R bits         R bits
 <---------------> <------------>
+-----------------+--------------+
| Key Generation  | Ratchet Step |
+-----------------+--------------+
~~~
{: #sender-keys-kid title="Structure of a KID in the Sender Keys Scheme" }

The sender signals such a ratchet step update by sending with a KID value in
which the ratchet step has been incremented.  A receiver who receives from a
sender with a new KID computes the new key as above.  The old key may be kept
for some time to allow for out-of-order delivery, but should be deleted
promptly.

If a new participant joins in the middle of a session, they will need to receive
from each sender (a) the current sender key for that sender and (b) the current
KID value for the sender. Evicting a participant requires each sender to send
a fresh sender key to all receivers.

It is up to the application to decide when sender keys are updated.  A sender
key may be updated by sending a new `base_key` (updating the key generation) or
by hashing the current `base_key` (updating the ratchet step).  Ratcheting the
key forward is useful when adding new receivers to an SFrame-based interaction,
since it ensures that the new receivers can't decrypt any media encrypted before
they were added.  If a sender wishes to assure the opposite property when
removing a receiver (i.e., ensuring that the receiver can't decrypt media after
they are removed), then the sender will need to distribute a new sender key.

## MLS

The Messaging Layer Security (MLS) protocol provides group authenticated key
exchange {{?MLS-ARCH=I-D.ietf-mls-architecture}} {{!MLS-PROTO=RFC9420}}.  In
principle, it could be used to instantiate the sender key scheme above, but it
can also be used more efficiently directly.

MLS creates a linear sequence of keys, each of which is shared among the members
of a group at a given point in time.  When a member joins or leaves the group, a
new key is produced that is known only to the augmented or reduced group.  Each
step in the lifetime of the group is known as an "epoch", and each member of the
group is assigned an "index" that is constant for the time they are in the
group.

To generate keys and nonces for SFrame, we use the MLS exporter function to
generate a `base_key` value for each MLS epoch.  Each member of the group is
assigned a set of KID values so that each member has a unique `sframe_key` and
`sframe_salt` that it uses to encrypt with.  Senders may choose any KID value
within their assigned set of KID values, e.g., to allow a single sender to send
multiple, uncoordinated outbound media streams.

~~~ pseudocode
base_key = MLS-Exporter("SFrame 1.0 Base Key", "", AEAD.Nk)
~~~

<!-- [rfced] Section 5.2. We are having difficulty parsing the following. Does the Receiver remove the old epoch? Should "the same E lower bits" be "the same low-order E bits"?

Original:
   Receivers MUST
   be prepared for the epoch counter to roll over, removing an old epoch
   when a new epoch with the same E lower bits is introduced.

Perhaps:
   Receivers MUST
   be prepared for the epoch counter to roll over and remove an old epoch
   when a new epoch with the same low-order E bits is introduced. -->

For compactness, we do not send the whole epoch number.  Instead, we send only
its low-order `E` bits, where `E` is a value set by the application.  `E`
effectively defines a reordering window, since no more than 2<sup>`E`</sup>
epochs can be active at a given time.  Receivers MUST be prepared for the epoch
counter to roll over, removing an old epoch when a new epoch with the same E
lower bits is introduced.

Let `S` be the number of bits required to encode a member index in the group,
i.e., the smallest value such that `group_size <= (1 << S)`.  The sender index
is encoded in the `S` bits above the epoch.  The remaining `64 - S - E` bits of
the KID value are a `context` value chosen by the sender (context value `0` will
produce the shortest encoded KID).

~~~ pseudocode
KID = (context << (S + E)) + (sender_index << E) + (epoch % (1 << E))
~~~

~~~ aasvg
  64-S-E bits   S bits   E bits
 <-----------> <------> <------>
+-------------+--------+-------+
| Context ID  | Index  | Epoch |
+-------------+--------+-------+
~~~
{: #mls-kid title="Structure of a KID for an MLS Sender" }

Once an SFrame stack has been provisioned with the `sframe_epoch_secret` for an
epoch, it can compute the required KID values on demand (as well as the
resulting SFrame keys/nonces derived from the `base_key` and KID) as it needs
to encrypt or decrypt for a given member.

~~~ aasvg
  ...
         |
         |
Epoch 14 +--+-- index=3 ---> KID = 0x3e
         |  |
         |  +-- index=7 ---> KID = 0x7e
         |  |
         |  +-- index=20 --> KID = 0x14e
         |
         |
Epoch 15 +--+-- index=3 ---> KID = 0x3f
         |  |
         |  +-- index=5 ---> KID = 0x5f
         |
         |
Epoch 16 +----- index=2 --+--> context = 2 --> KID = 0x820
         |                |
         |                +--> context = 3 --> KID = 0xc20
         |
         |
Epoch 17 +--+-- index=33 --> KID = 0x211
         |  |
         |  +-- index=51 --> KID = 0x331
         |
         |
  ...
~~~
{: #mls-evolution title="An Example Sequence of KIDs for an MLS-based SFrame
Session (E=4; S=6, Allowing for 64 Group Members)" }

# Media Considerations

## Selective Forwarding Units

SFUs (e.g., those described in {{Section 3.7 of
?RFC7667}}) receive the media streams from each participant and select which
ones should be forwarded to each of the other participants.  There are several
approaches for stream selection, but in general, the SFU needs to access
metadata associated with each frame and modify the RTP information of the incoming
packets when they are transmitted to the received participants.

This section describes how these normal SFU modes of operation interact with the
E2EE provided by SFrame.

### LastN and RTP Stream Reuse

<!--[rfced] Section 6.1.1. The term "LastN" is used in the title of the section ("LastN and RTP Stream Reuse"), but it is not expanded or otherwise explained within the section. How may we make this term clearer to the reader? -->

The SFU may choose to send only a certain number of streams based on the voice
activity of the participants. To avoid the overhead involved in establishing new
transport streams, the SFU may decide to reuse previously existing streams or
even pre-allocate a predefined number of streams and choose in each moment in
time which participant media will be sent through it.

<!--[rfced] Section 6.1.1. The clause in the following sentence appears to be missing a subject: it's unclear what is carrying the media.

Original:
   This means that in the same transport-level stream (e.g., an RTP
   stream defined by either SSRC or MID) may carry media from different
   streams of different participants.

Perhaps (removing the preposition "in" so that "the same transport-level stream" becomes the subject and expanding "MID"):
   This means that the same transport-level stream (e.g., an RTP
   stream defined by either SSRC or Media Identification (MID)) may 
   carry media from different streams of different participants. -->

<!--[rfced] Section 6.1.1. Does the following proposed update improve the readability of the sentence?

Original:
   As different keys are used by each participant for encoding their media, 
   the receiver will be able to verify which is the sender of the media 
   coming within the RTP stream at any given point in time, preventing the 
   SFU trying to impersonate any of the participants with another 
   participant's media.

Perhaps:
   Because each participant uses a different key to encode their media,
   the receiver will be able to verify the sender of the media within 
   the RTP stream at any given point in time, which prevents any attempt 
   by the SFU to impersonate a participant with another participant's 
   media. -->

This means that in the same transport-level stream (e.g., an RTP stream defined
by either SSRC or Media Identification (MID)) may carry media from different streams of different
participants. As different keys are used by each participant for encoding their
media, the receiver will be able to verify which is the sender of the media
coming within the RTP stream at any given point in time, preventing the SFU
trying to impersonate any of the participants with another participant's media.

Note that in order to prevent impersonation by a malicious participant (not the
SFU), a mechanism based on digital signature would be required. SFrame does not
protect against such attacks.

### Simulcast

When using simulcast, the same input image will produce N different encoded
frames (one per simulcast layer), which would be processed independently by the
frame encryptor and assigned an unique counter for each.

### SVC

In both temporal and spatial scalability, the SFU may choose to drop layers in
order to match a certain bitrate or to forward specific media sizes or frames per
second. In order to support the SFU selectively removing layers, the sender MUST
encapsulate each layer in a different SFrame ciphertext.

## Video Key Frames

Forward security and post-compromise security require that the E2EE keys (base keys)
are updated any time a participant joins or leaves the call.

The key exchange happens asynchronously and on a different path than the SFU signaling
and media. So it may happen that, when a new participant joins the call and the
SFU side requests a key frame, the sender generates the E2EE frame
with a key that is not known by the receiver, so it will be discarded. When the sender
updates his sending key with the new key, it will send it in a non-key frame, so
the receiver will be able to decrypt it, but not decode it.

The new receiver will then re-request a key frame, but due to sender and SFU
policies, that new key frame could take some time to be generated.

If the sender sends a key frame after the new E2EE key is in use, the time
required for the new participant to display the video is minimized.

Note that this issue does not arise for media streams that do not have
dependencies among frames, e.g., audio streams.  In these streams, each frame is
independently decodable, so there is never a need to process together two frames
that might be on two sides of a key rotation.

## Partial Decoding

Some codecs support partial decoding, where individual packets can be decoded
without waiting for the full frame to arrive.  When SFrame is applied per frame,
partial decoding is not possible because the decoder cannot access data until an entire
frame has arrived and has been decrypted.

# Security Considerations

## No Header Confidentiality

SFrame provides integrity protection to the SFrame header (the Key ID and
counter values), but it does not provide confidentiality protection.  Parties that
can observe the SFrame header may learn, for example, which parties are sending
SFrame payloads (from KID values) and at what rates (from CTR values).  In cases
where SFrame is used for end-to-end security on top of hop-by-hop protections
(e.g., running over SRTP as described in {{sframe-over-rtp}}), the hop-by-hop security
mechanisms provide confidentiality protection of the SFrame header between hops.

## No per-Sender Authentication

SFrame does not provide per-sender authentication of media data.  Any sender in
a session can send media that will be associated with any other sender.  This is
because SFrame uses symmetric encryption to protect media data, so that any
receiver also has the keys required to encrypt packets for the sender.

## Key Management

The key exchange mechanism is out of scope of this document; however, every client
SHOULD change their keys when new clients join or leave the call for forward
secrecy and post-compromise security.

## Replay

The handling of replay is out of the scope of this document. However, senders
MUST reject requests to encrypt multiple times with the same key and nonce
since several AEAD algorithms fail badly in such cases (see, e.g., {{Section 5.1.1 of RFC5116}}).

## Risks Due to Short Tags

The SFrame cipher suites based on AES-CTR allow for the use of short
authentication tags, which bring a higher risk that an attacker will be
able to cause an SFrame receiver to accept an SFrame ciphertext of the
attacker's choosing.

Assuming that the authentication properties of the cipher suite are robust, the
only attack that an attacker can mount is an attempt to find an acceptable
(ciphertext, tag) combination through brute force.  Such a brute-force attack
will have an expected success rate of the following form:

```
attacker_success_rate = attempts_per_second / 2^(8*Nt)
```

For example, a gigabit Ethernet connection is able to transmit roughly 2<sup>20</sup>
packets per second.  If an attacker saturated such a link with guesses against a
32-bit authentication tag (`Nt=4`), then the attacker would succeed on average
roughly once every 2<sup>12</sup> seconds, or about once an hour.

In a typical SFrame usage in a real-time media application, there are a few
approaches to mitigating this risk:

* Receivers only accept SFrame ciphertexts over HBH-secure channels (e.g., SRTP
  security associations or QUIC connections).  If this is the case, only an
  entity that is part of such a channel can mount the above attack.

* The expected packet rate for a media stream is very predictable (and typically
  far lower than the above example).  On the one hand, attacks at this rate will
  succeed even less often than the high-rate attack described above.  On the
  other hand, the application may use an elevated packet-arrival rate as a
  signal of a brute-force attack.  This latter approach is common in other
  settings, e.g., mitigating brute-force attacks on passwords.

* Media applications typically do not provide feedback to media senders as to
  which media packets failed to decrypt.  When media-quality feedback
  mechanisms are used, decryption failures will typically appear as packet
  losses, but only at an aggregate level.

* Anti-replay mechanisms (see {{replay}}) prevent the attacker from reusing
  valid ciphertexts (either observed or guessed by the attacker).  A receiver
  applying anti-replay controls will only accept one valid plaintext per CTR
  value.  Since the CTR value is covered by SFrame authentication, an attacker
  has to do a fresh search for a valid tag for every forged ciphertext, even if
  the encrypted content is unchanged.  In other words, when the above brute-force
  attack succeeds, it only allows the attacker to send a single SFrame
  ciphertext; the ciphertext cannot be reused because either it will have the
  same CTR value and be discarded as a replay, or else it will have a different
  CTR value and its tag will no longer be valid.

Nonetheless, without these mitigations, an application that makes use of short
tags will be at heightened risk of forgery attacks.  In many cases, it is
simpler to use full-size tags and tolerate slightly higher-bandwidth usage
rather than to add the additional defenses necessary to safely use short tags.

# IANA Considerations

IANA has created a new registry called "SFrame Cipher Suites" ({{sframe-cipher-suites}})
under the "SFrame" group registry heading.  Assignments are made
via the Specification Required policy {{!RFC8126}}.

<!-- [rfced] IANA Considerations. The text indicates the that registration policy for the "SFrame Cipher Suites" is Specification Required.  However, it later refers to Standards Action and Private Use, and the IANA registry includes ranges for Standards Action and Private Use.  Are the ranges as defined on the IANA page correct?  For clarity, may we specify the ranges as follows?  In addition, perhaps the text should be moved to Section 8.1, appearing after the valid range of cipher suites is noted.  

Original:
   This registry should be under a heading of "SFrame", and assignments
   are made via the Specification Required policy [RFC8126].

Perhaps: 
   IANA has created a new registry called "SFrame Cipher Suites" (Section 8.1)
   under the "SFrame" group registry heading.  Assignments are made per the following 
   registration procedures [RFC8126]: 
   
   0-0xEFFF  Specification Required
   0-0xEFFF  Standards Action
   0xF000-0xFFFF  Private Use
-->    

## SFrame Cipher Suites

The "SFrame Cipher Suites" registry lists identifiers for SFrame cipher suites as defined in
{{cipher-suites}}.  The cipher suite field is two bytes wide, so the valid cipher
suites are in the range 0x0000 to 0xFFFF.

The registration template is as follows:

* Value: The numeric value of the cipher suite

* Name: The name of the cipher suite

* Recommended: Whether support for this cipher suite is recommended by the IETF.
  Valid values are "Y", "N", and "D" as described in {{Section 17.1 of
  MLS-PROTO}}. The default value of the "Recommended" column is "N". Setting the
  Recommended item to "Y" or "D", or changing an item whose current value is "Y"
  or "D", requires Standards Action {{RFC8126}}.

* Reference: The document where this cipher suite is defined

* Change Controller: Who is authorized to update the row in the registry

<!--[rfced] IANA Considerations. FYI, we have added "Change Controller" to the registry template and table as IANA has added this column to the "SFrame Cipher Suites" registry. Please review. -->

Initial contents:


| Value           | Name                          | R | Reference | Change Controller |
|:----------------|:------------------------------|:--|:----------|:------------------|
| 0x0000          | Reserved                      | - | RFC 9605  | IETF              |
| 0x0001          | `AES_128_CTR_HMAC_SHA256_80`  | Y | RFC 9605  | IETF              |
| 0x0002          | `AES_128_CTR_HMAC_SHA256_64`  | Y | RFC 9605  | IETF              |
| 0x0003          | `AES_128_CTR_HMAC_SHA256_32`  | Y | RFC 9605  | IETF              |
| 0x0004          | `AES_128_GCM_SHA256_128`      | Y | RFC 9605  | IETF              |
| 0x0005          | `AES_256_GCM_SHA512_128`      | Y | RFC 9605  | IETF              |
| 0xF000 - 0xFFFF | Reserved for Private Use      | - | RFC 9605  | IETF              |
{: #iana-cipher-suites title="SFrame Cipher Suites" }

# Application Responsibilities

To use SFrame, an application needs to define the inputs to the SFrame
encryption and decryption operations, and how SFrame ciphertexts are delivered
from sender to receiver (including any fragmentation and reassembly).  In this
section, we lay out additional requirements that an implementation must meet in
order for SFrame to operate securely.

In general, an application using SFrame is responsible for configuring SFrame.
The application must first define when SFrame is applied at all.  When SFrame is
applied, the application must define which cipher suite is to be used.  If new
versions of SFrame are defined in the future, it will be up to the application
to determine which version should be used.

This division of responsibilities is similar to the way other media parameters
(e.g., codecs) are typically handled in media applications, in the sense that
they are set up in some signaling protocol and not described in the media.
Applications might find it useful to extend the protocols used for negotiating
other media parameters (e.g., Session Description Protocol (SDP) {{?RFC8866}}) to also negotiate parameters for
SFrame.

## Header Value Uniqueness

Applications MUST ensure that each (`base_key`, KID, CTR) combination is used
for at most one SFrame encryption operation. This ensures that the (key, nonce)
pairs used by the underlying AEAD algorithm are never reused. Typically this is
done by assigning each sender a KID or set of KIDs, then having each sender use
the CTR field as a monotonic counter, incrementing for each plaintext that is
encrypted. In addition to its simplicity, this scheme minimizes overhead by
keeping CTR values as small as possible.

In applications where an SFrame context might be written to persistent storage,
this context needs to include the last-used CTR value.  When the context is used
later, the application should use the stored CTR value to determine the next CTR
value to be used in an encryption operation, and then write the next CTR value
back to storage before using the CTR value for encryption.  Storing the CTR
value before usage (vs. after) helps ensure that a storage failure will not
cause reuse of the same (`base_key`, KID, CTR) combination.

## Key Management Framework

It is up to the application to provision SFrame with a mapping of KID values to
`base_key` values and the resulting keys and salts.  More importantly, the
application specifies which KID values are used for which purposes (e.g., by
which senders).  An application's KID assignment strategy MUST be structured to
assure the non-reuse properties discussed in {{header-value-uniqueness}}.

It is also up to the application to define a rotation schedule for keys.  For
example, one application might have an ephemeral group for every call and keep
rotating keys when endpoints join or leave the call, while another application
could have a persistent group that can be used for multiple calls and simply
derives ephemeral symmetric keys for a specific call.

It should be noted that KID values are not encrypted by SFrame and are thus
visible to any application-layer intermediaries that might handle an SFrame
ciphertext.  If there are application semantics included in KID values, then
this information would be exposed to intermediaries.  For example, in the scheme
of {{sender-keys}}, the number of ratchet steps per sender is exposed, and in
the scheme of {{mls}}, the number of epochs and the MLS sender ID of the SFrame
sender are exposed.

## Anti-Replay

It is the responsibility of the application to handle anti-replay. Replay by network
attackers is assumed to be prevented by network-layer facilities (e.g., TLS, SRTP).
As mentioned in {{replay}}, senders MUST reject requests to encrypt multiple times
with the same key and nonce.

It is not mandatory to implement anti-replay on the receiver side. Receivers MAY
apply time- or counter-based anti-replay mitigations.  For example, {{Section
3.3.2 of ?RFC3711}} specifies a counter-based anti-replay mitigation, which
could be adapted to use with SFrame, using the CTR field as the counter.

## Metadata

<!--[rfced] Section 9.4. It is unclear what "pure" means in the following sentence. Is the metadata only specified by the application? Please help us clarify.

Original:
   The metadata input to SFrame operations is pure application-specified
   data. -->

The `metadata` input to SFrame operations is pure application-specified data. As
such, it is up to the application to define what information should go in the
`metadata` input and ensure that it is provided to the encryption and decryption
functions at the appropriate points.  A receiver MUST NOT use SFrame-authenticated
metadata until after the SFrame decrypt function has authenticated it, unless
the purpose of such usage is to prepare an SFrame ciphertext for SFrame
decryption.  Essentially, metadata may be used "upstream of SFrame" in a
processing pipeline, but only to prepare for SFrame decryption.

For example, consider an application where SFrame is used to encrypt audio
frames that are sent over SRTP, with some application data included in the RTP
header extension. Suppose the application also includes this application data in
the SFrame metadata, so that the SFU is allowed to read, but not modify, the
application data.  A receiver can use the application data in the RTP header
extension as part of the standard SRTP decryption process since this is
required to recover the SFrame ciphertext carried in the SRTP payload.  However,
the receiver MUST NOT use the application data for other purposes before SFrame
decryption has authenticated the application data.

--- back
<!--Informative References:
[I-D.codec-agnostic-rtp-payload-format] replaced by draft-gouaillard-avtcore-codec-agn-rtp-payload, which is expired.
[I-D.ietf-moq-transport] Active WG document
[I-D.ietf-webtrans-overview] Active WG document
[MLS-ARCH] Active WG document -->

# Example API

**This section is not normative.**

This section describes a notional API that an SFrame implementation might
expose.  The core concept is an "SFrame context", within which KID values are
meaningful.  In the key management scheme described in {{sender-keys}}, each
sender has a different context; in the scheme described in {{mls}}, all senders
share the same context.

An SFrame context stores mappings from KID values to "key contexts", which are
different depending on whether the KID is to be used for sending or receiving
(an SFrame key should never be used for both operations).  A key context tracks
the key and salt associated to the KID, and the current CTR value.  A key
context to be used for sending also tracks the next CTR value to be used.

The primary operations on an SFrame context are as follows:

* **Create an SFrame context:** The context is initialized with a cipher suite and
  no KID mappings.
* **Add a key for sending:** The key and salt are derived from the base key, and
  are used to initialize a send context, together with a zero counter value.
* **Add a key for receiving:** The key and salt are derived from the base key, and
  are used to initialize a send context.
* **Encrypt a plaintext:** Encrypt a given plaintext using the key for a given KID,
  including the specified metadata.
* **Decrypt an SFrame ciphertext:** Decrypt an SFrame ciphertext with the KID
  and CTR values specified in the SFrame header, and the provided metadata.

{{rust-api}} shows an example of the types of structures and methods that could
be used to create an SFrame API in Rust.

~~~ rust
type KeyId = u64;
type Counter = u64;
type CipherSuite = u16;

struct SendKeyContext {
  key: Vec<u8>,
  salt: Vec<u8>,
  next_counter: Counter,
}

struct RecvKeyContext {
  key: Vec<u8>,
  salt: Vec<u8>,
}

struct SFrameContext {
  cipher_suite: CipherSuite,
  send_keys: HashMap<KeyId, SendKeyContext>,
  recv_keys: HashMap<KeyId, RecvKeyContext>,
}

trait SFrameContextMethods {
  fn create(cipher_suite: CipherSuite) -> Self;
  fn add_send_key(&self, kid: KeyId, base_key: &[u8]);
  fn add_recv_key(&self, kid: KeyId, base_key: &[u8]);
  fn encrypt(&mut self, kid: KeyId, metadata: &[u8],
             plaintext: &[u8]) -> Vec<u8>;
  fn decrypt(&self, metadata: &[u8], ciphertext: &[u8]) -> Vec<u8>;
}
~~~
{: #rust-api title="An Example SFrame API" }

# Overhead Analysis

Any use of SFrame will impose overhead in terms of the amount of bandwidth
necessary to transmit a given media stream.  Exactly how much overhead will be added
depends on several factors:

* The number of senders involved in a conference (length of KID)
* The duration of the conference (length of CTR)
* The cipher suite in use (length of authentication tag)
* Whether SFrame is used to encrypt packets, whole frames, or some other unit

Overall, the overhead rate in kilobits per second can be estimated as:

```
OverheadKbps = (1 + |CTR| + |KID| + |TAG|) * 8 * CTPerSecond / 1024
```

Here the constant value `1` reflects the fixed SFrame header; `|CTR|` and
`|KID|` reflect the lengths of those fields; `|TAG|` reflects the cipher
overhead; and `CTPerSecond` reflects the number of SFrame ciphertexts
sent per second (e.g., packets or frames per second).

In the remainder of this section, we compute overhead estimates for a collection
of common scenarios.

## Assumptions

In the below calculations, we make conservative assumptions about SFrame
overhead so that the overhead amounts we compute here are likely to be an upper
bound of those seen in practice.

<!--[rfced] Section B.1. FYI, we added a title to Table 3.

Current:
  Table 3:  Overhead Analysis Assumptions
-->

| Field           | Bytes | Explanation                                       |
|:----------------|------:|:--------------------------------------------------|
| Fixed header    | 1     | Fixed                                             |
| Key ID (KID)    | 2     | >255 senders; or MLS epoch (E=4) and >16 senders  |
| Counter (CTR)   | 3     | More than 24 hours of media in common cases       |
| Cipher overhead | 16    | Full Galois/Counter Mode (GCM) tag (longest defined here)  |
{: #analysis-assumptions title="Overhead Analysis Assumptions" }

In total, then, we assume that each SFrame encryption will add 22 bytes of
overhead.

We consider two scenarios: applying SFrame per frame and per packet.  In each
scenario, we compute the SFrame overhead in absolute terms (kbps) and as a
percentage of the base bandwidth.

## Audio

In audio streams, there is typically a one-to-one relationship between frames
and packets, so the overhead is the same whether one uses SFrame at a per-packet
or per-frame level.

{{audio-overhead}} considers three scenarios that are based on recommended configurations
of the Opus codec {{?RFC6716}}:

* Narrow-band (NB) speech: 120 ms packets, 8 kbps
* Full-band (FB) speech: 20 ms packets, 32 kbps
* Full-band stereo music: 10 ms packets, 128 kbps

| Scenario                  | Frames per Second (fps) | Base kbps | Overhead kbps | Overhead % |
|:--------------------------|:---:|:---------:|:-------------:|:----------:|
| NB speech, 120 ms packets | 8.3 |         8 |           1.4 |      17.9% |
| FB speech, 20 ms packets  |  50 |        32 |           8.6 |      26.9% |
| FB stereo, 10 ms packets  | 100 |       128 |          17.2 |      13.4% |
{: #audio-overhead title="SFrame Overhead for Audio Streams" }

## Video

Video frames can be larger than an MTU and thus are commonly split across
multiple frames.  {{video-overhead-per-frame}} and {{video-overhead-per-packet}}
show the estimated overhead of encrypting a video stream, where SFrame is
applied per frame and per packet, respectively.  The choices of resolution,
frames per second, and bandwidth roughly reflect the capabilities of
modern video codecs across a range from very-low to very-high quality.

| Scenario    | fps | Base kbps | Overhead kbps | Overhead % |
|:------------|:---:|:---------:|:-------------:|:----------:|
| 426 x 240   | 7.5 |        45 |           1.3 |       2.9% |
| 640 x 360   |  15 |       200 |           2.6 |       1.3% |
| 640 x 360   |  30 |       400 |           5.2 |       1.3% |
| 1280 x 720  |  30 |      1500 |           5.2 |       0.3% |
| 1920 x 1080 |  60 |      7200 |          10.3 |       0.1% |
{: #video-overhead-per-frame title="SFrame Overhead for a Video Stream Encrypted per Frame" }

| Scenario    | fps | Packets per Second (pps) | Base kbps | Overhead kbps | Overhead % |
|:------------|:---:|:---:|:---------:|:-------------:|:----------:|
| 426 x 240   | 7.5 | 7.5 |        45 |           1.3 |       2.9% |
| 640 x 360   |  15 |  30 |       200 |           5.2 |       2.6% |
| 640 x 360   |  30 |  60 |       400 |          10.3 |       2.6% |
| 1280 x 720  |  30 | 180 |      1500 |          30.9 |       2.1% |
| 1920 x 1080 |  60 | 780 |      7200 |         134.1 |       1.9% |
{: #video-overhead-per-packet title="SFrame Overhead for a Video Stream Encrypted per Packet" }

In the per-frame case, the SFrame percentage overhead approaches zero as the
quality of the video improves since bandwidth is driven more by picture size
than frame rate.  In the per-packet case, the SFrame percentage overhead
approaches the ratio between the SFrame overhead per packet and the MTU (here 22
bytes of SFrame overhead divided by an assumed 1200-byte MTU, or about 1.8%).

## Conferences

Real conferences usually involve several audio and video streams.  The overhead
of SFrame in such a conference is the aggregate of the overhead of all the
individual streams.  Thus, while SFrame incurs a large percentage overhead on an
audio stream, if the conference also involves a video stream, then the audio
overhead is likely negligible relative to the overall bandwidth of the
conference.

For example, {{conference-overhead}} shows the overhead estimates for a two-person
conference where one person is sending low-quality media and the other is
sending high-quality media.  (And we assume that SFrame is applied per frame.)  The
video streams dominate the bandwidth at the SFU, so the total bandwidth overhead
is only around 1%.

| Stream                 | Base Kbps | Overhead Kbps | Overhead % |
|:-----------------------|:---------:|:-------------:|:----------:|
| Participant 1 audio    |         8 |           1.4 |      17.9% |
| Participant 1 video    |        45 |           1.3 |       2.9% |
| Participant 2 audio    |        32 |           9   |      26.9% |
| Participant 2 video    |      1500 |           5   |       0.3% |
| Total at SFU           |      1585 |          16.5 |       1.0% |
{: #conference-overhead title="SFrame Overhead for a Two-Person Conference" }

## SFrame over RTP

SFrame is a generic encapsulation format, but many of the applications in which
it is likely to be integrated are based on RTP.  This section discusses how an
integration between SFrame and RTP could be done, and some of the challenges
that would need to be overcome.

As discussed in {{application-context}}, there are two natural patterns for
integrating SFrame into an application: applying SFrame per frame or per packet.
In RTP-based applications, applying SFrame per packet means that the payload of
each RTP packet will be an SFrame ciphertext, starting with an SFrame header, as
shown in {{sframe-packet}}.  Applying SFrame per frame means that different
RTP payloads will have different formats: the first payload of a frame will
contain the SFrame headers, and subsequent payloads will contain further chunks
of the ciphertext, as shown in {{sframe-multi-packet}}.

In order for these media payloads to be properly interpreted by receivers,
receivers will need to be configured to know which of the above schemes the
sender has  applied to a given sequence of RTP packets. SFrame does not provide
a mechanism for distributing this configuration information. In applications
that use SDP for negotiating RTP media streams {{?RFC8866}}, an appropriate
extension to SDP could provide this function.

<!--[rfced] Section B.5. draft-codec-agnostic-rtp-payload-format has been replaced by draft-gouaillard-avtcore-codec-agn-rtp-payload (which expired Sept 2021). Do you want to replace the reference?

Original:
   In order for such a generic packetization scheme to work
   interoperably one would have to be defined, e.g., as proposed in
   [I-D.codec-agnostic-rtp-payload-format].
-->

Applying SFrame per frame also requires that packetization and depacketization
be done in a generic manner that does not depend on the media content of the
packets, since the content being packetized/depacketized will be opaque
ciphertext (except for the SFrame header).  In order for such a generic
packetization scheme to work interoperably, one would have to be defined, e.g.,
as proposed in {{?I-D.codec-agnostic-rtp-payload-format}}.

~~~ aasvg
   +---+-+-+-------+-+-------------+-------------------------------+<-+
   |V=2|P|X|  CC   |M|     PT      |       sequence number         |  |
   +---+-+-+-------+-+-------------+-------------------------------+  |
   |                           timestamp                           |  |
   +---------------------------------------------------------------+  |
   |           synchronization source (SSRC) identifier            |  |
   +===============================================================+  |
   |            contributing source (CSRC) identifiers             |  |
   |                               ....                            |  |
   +---------------------------------------------------------------+  |
   |                   RTP extension(s) (OPTIONAL)                 |  |
+->+--------------------+------------------------------------------+  |
|  |   SFrame header    |                                          |  |
|  +--------------------+                                          |  |
|  |                                                               |  |
|  |          SFrame encrypted and authenticated payload           |  |
|  |                                                               |  |
+->+---------------------------------------------------------------+<-+
|  |                    SRTP authentication tag                    |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
+--- SRTP Encrypted Portion             SRTP Authenticated Portion ---+
~~~
{: #sframe-packet title="SRTP Packet with SFrame-Protected Payload"}

~~~ aasvg
   +----------------+  +---------------+
   | frame metadata |  |               |
   +-------+--------+  |               |
           |           |     frame     |
           |           |               |
           |           |               |
           |           +-------+-------+
           |                   |
           |                   |
           V                   V
+--------------------------------------+
|            SFrame Encrypt            |
+--------------------------------------+
   |                           |
   |                           |
   |                           V
   |                   +-------+-------+
   |                   |               |
   |                   |               |
   |                   |   encrypted   |
   |                   |     frame     |
   |                   |               |
   |                   |               |
   |                   +-------+-------+
   |                           |
   |                  generic RTP packetize
   |                           |
   |    +----------------------+--------.....--------+
   |    |                      |                     |
   V    V                      V                     V
+---------------+      +---------------+     +---------------+
| SFrame header |      |               |     |               |
+---------------+      |               |     |               |
|               |      |  payload 2/N  | ... |  payload N/N  |
|  payload 1/N  |      |               |     |               |
|               |      |               |     |               |
+---------------+      +---------------+     +---------------+
~~~
{: #sframe-multi-packet title="Encryption Flow with per-Frame Encryption for RTP" }

# Test Vectors

This section provides a set of test vectors that implementations can use to
verify that they correctly implement SFrame encryption and decryption.  In
addition to test vectors for the overall process of SFrame
encryption/decryption, we also provide test vectors for header
encoding/decoding, and for AEAD encryption/decryption using the AES-CTR
construction defined in {{aes-ctr-with-sha2}}.

All values are either numeric or byte strings.  Numeric values are represented
as hex values, prefixed with `0x`.  Byte strings are represented in hex
encoding.

Line breaks and whitespace within values are inserted to conform to the width
requirements of the RFC format.  They should be removed before use.

These test vectors are also available in JSON format at {{TestVectors}}.  In the
JSON test vectors, numeric values are JSON numbers and byte string values are
JSON strings containing the hex encoding of the byte strings.

## Header Encoding/Decoding

For each case, we provide:

* `kid`: A KID value
* `ctr`: A CTR value
* `header`: An encoded SFrame header

An implementation should verify that:

* Encoding a header with the KID and CTR results in the provided header value
* Decoding the provided header value results in the provided KID and CTR values

{::include test-vectors/header.md}


## AEAD Encryption/Decryption Using AES-CTR and HMAC

For each case, we provide:

* `cipher_suite`: The index of the cipher suite in use (see
  {{sframe-cipher-suites}})
* `key`: The `key` input to encryption/decryption
* `enc_key`: The encryption subkey produced by the `derive_subkeys()` algorithm
* `auth_key`: The encryption subkey produced by the `derive_subkeys()` algorithm
* `nonce`: The `nonce` input to encryption/decryption
* `aad`: The `aad` input to encryption/decryption
* `pt`: The plaintext
* `ct`: The ciphertext

An implementation should verify that the following are true, where
`AEAD.Encrypt` and `AEAD.Decrypt` are as defined in {{aes-ctr-with-sha2}}:

* `AEAD.Encrypt(key, nonce, aad, pt) == ct`
* `AEAD.Decrypt(key, nonce, aad, ct) == pt`

The other values in the test vector are intermediate values provided to
facilitate debugging of test failures.

{::include test-vectors/aes-ctr-hmac.md}

## SFrame Encryption/Decryption

For each case, we provide:

* `cipher_suite`: The index of the cipher suite in use (see
  {{sframe-cipher-suites}})
* `kid`: A KID value
* `ctr`: A CTR value
* `base_key`: The `base_key` input to the `derive_key_salt` algorithm
* `sframe_key_label`: The label used to derive `sframe_key` in the `derive_key_salt` algorithm
* `sframe_salt_label`: The label used to derive `sframe_salt` in the `derive_key_salt` algorithm
* `sframe_secret`: The `sframe_secret` variable in the `derive_key_salt` algorithm
* `sframe_key`: The `sframe_key` value produced by the `derive_key_salt` algorithm
* `sframe_salt`: The `sframe_salt` value produced by the `derive_key_salt` algorithm
* `metadata`: The `metadata` input to the SFrame `encrypt` algorithm
* `pt`: The plaintext
* `ct`: The SFrame ciphertext

An implementation should verify that the following are true, where
`encrypt` and `decrypt` are as defined in {{encryption-schema}}, using an SFrame
context initialized with `base_key` assigned to `kid`:

* `encrypt(ctr, kid, metadata, plaintext) == ct`
* `decrypt(metadata, ct) == pt`

The other values in the test vector are intermediate values provided to
facilitate debugging of test failures.

{::include test-vectors/sframe.md}

# Acknowledgements
{: numbered="false"}

The authors wish to specially thank {{{Dr. Alex Gouaillard}}} as one of the early
contributors to the document. His passion and energy were key to the design and
development of SFrame.

<!--[rfced] Terminology. 

a) FYI, we have added expansions for abbreviations upon first use per Section 3.6 of RFC 7322 ("RFC Style Guide"). Please review each expansion in the document carefully to ensure correctness.

b) Please help us expand or define the following term:

   SVC

c) May we make the use of the acronym KID consistent?

   Key ID (13) / KID (85)

d) Please help us make the capitalization of the following terms consistent

   counter (22) / Counter (9) - We note that Key ID is capitalized.
                                Should CTR be used instead?

e) Please review the use of fixed-width format for the following terms and let us know if any updates are necessary:

   context, when referring to a value
   CTR
   key, when referring to input
   KID
   nonce

f) As "up to" may be difficult for ESL readers to understand, may we update the use of the phrase "it is up to the application" to "it is the application's responsibility"?

Original:
Section 5.1: 
   It is up to the application to decide when sender keys are updated.

Section 9:
   If new versions of SFrame are
   defined in the future, it will be up to the application to determine
   which version should be used.

Section 9.2:
   It is up to the application to provision SFrame with a mapping of KID
   values to base_key values and the resulting keys and salts.
   ...
   It is also up to the application to define a rotation schedule for
   keys.  

Section 9.4:
   As such, it is up to the application to define what
   information should go in the metadata input and ensure that it is
   provided to the encryption and decryption functions at the
   appropriate points.  

Perhaps:
Section 5.1: 
   It is the application's responsibility to decide when sender keys are updated.

Section 9:
   If new versions of SFrame are
   defined in the future, it is the application's responsibility to determine
   which version should be used.

Section 9.2:
   It is the application's responsibility to provision SFrame with a mapping of KID
   values to base_key values and the resulting keys and salts.
   ...
   It is also the application's responsibility to define a rotation schedule for
   keys.  

Section 9.4:
   As such, it the application's responsibility to define what
   information should go in the metadata input and ensure that it is
   provided to the encryption and decryption functions at the
   appropriate points.  
-->

<!--[rfced] Please review the "Inclusive Language" portion of the online Style Guide <https://www.rfc-editor.org/styleguide/part2/#inclusive_language> and let us know if any changes are needed. For example, please consider whether the following should be updated: whitespace 
-->

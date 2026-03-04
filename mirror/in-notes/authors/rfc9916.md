---
title: "Updates for PCEPS: TLS Connection Establishment Restrictions"
abbrev: Updates for PCEPS
category: std
updates: 8253

docname: draft-ietf-pce-pceps-tls13-latest
submissiontype: IETF
consensus: true
v: 3
area: "Routing"
workgroup: "Path Computation Element"
keyword:
 - PCEP
 - PCEPS
 - TLS 1.3
 - TLS 1.2
 - Early Data
 - 0-RTT
venue:
  group: "Path Computation Element"
  type: "Working Group"
  mail: "pce@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/pce/"
  github: "ietf-wg-pce/draft-ietf-pce-pceps-tls13"

author:
 -
    ins: D. Dhody
    name: Dhruv Dhody
    organization: Huawei
    email: dhruv.ietf@gmail.com
 -
    ins: S. Turner
    name: Sean Turner
    organization: sn3rd
    email: sean@sn3rd.com
 -
    name: Russ Housley
    org: Vigil Security, LLC
    abbrev: Vigil Security
    street: 516 Dranesville Road
    city: Herndon, VA
    code: 20170
    country: US
    email: housley@vigilsec.com

--- abstract

Section 3.4 of RFC 8253 specifies TLS connection establishment restrictions
for PCEPS; PCEPS refers to usage of TLS to provide a secure transport for
PCEP (Path Computation Element Communication Protocol).  This document adds
restrictions to specify what PCEPS implementations do if they support
more than one version of the TLS protocol and to restrict the use of
TLS 1.3's early data.


--- middle

# Introduction

{{Section 3.4 of !RFC8253}} specifies TLS connection establishment
restrictions for PCEPS; PCEPS refers to usage of TLS to
provide a secure transport for PCEP (Path Computation Element
Communication Protocol) {{!RFC5440}}.  This document adds restrictions to specify
what PCEPS implementations do if they support more than one version of
the TLS protocol, e.g., TLS 1.2 {{!RFC5246}} and
TLS 1.3 {{!I-D.ietf-tls-rfc8446bis}}, and to restrict the use of
TLS 1.3's early data, which is also known as 0-RTT data. All other
provisions set forth in {{RFC8253}} are unchanged, including connection
initiation, message framing, connection closure, certificate validation,
peer identity, and failure handling.


# Conventions and Definitions

{::boilerplate bcp14-tagged}


# TLS Connection Establishment Restrictions

{{Section 3.4 of RFC8253}} Step 1 includes restrictions on PCEPS TLS connection
establishment. This document adds the following restrictions:

* Implementations that support multiple versions of the TLS protocol MUST
prefer to negotiate the latest version of the TLS protocol; see
{{Section 4.2.1 of I-D.ietf-tls-rfc8446bis}}.

* PCEPS implementations that support TLS 1.3 or later MUST NOT use early data.

NOTE:
: Early data (aka 0-RTT data) is a mechanism defined in TLS 1.3
  {{I-D.ietf-tls-rfc8446bis}} that allows a client to send data ("early
  data") as part of the first flight of messages to a server.  Note
  that TLS 1.3 can be used without early data as per Appendix F.5 of
  {{I-D.ietf-tls-rfc8446bis}}.  In fact, early data is permitted by TLS
  1.3 only when the client and server share a Pre-Shared Key (PSK),
  either obtained externally or via a previous handshake.  The client
  uses the PSK to authenticate the server and to encrypt the early
  data.

NOTE:
: As noted in {{Section 2.3 of I-D.ietf-tls-rfc8446bis}}, the security
  properties for early data are weaker than those for subsequent TLS-
  protected data.  In particular, early data is not forward secret, and
  there is no protection against the replay of early data between
  connections.  {{Appendix E.5 of I-D.ietf-tls-rfc8446bis}} requires
  applications not use early data without a profile that defines its
  use.

# Security Considerations

The Security Considerations of PCEP {{RFC5440}}, {{?RFC8231}}, {{RFC8253}},
{{?RFC8281}}, and {{?RFC8283}}; TLS 1.2 {{RFC5246}}; TLS 1.3 {{I-D.ietf-tls-rfc8446bis}},
and; {{!RFC9325}} apply here as well.

# IANA Considerations

There are no IANA considerations.

# Implementation Status

<aside markdown="block">
  Note to the RFC Editor - remove this section before publication, as
  well as remove the reference to RFC 7942.
</aside>

This section records the status of known implementations of the
protocol defined by this specification at the time of posting of this
Internet-Draft, and is based on a proposal described in {{?RFC7942}}.
The description of implementations in this section is intended to
assist the IETF in its decision processes in progressing drafts to
RFCs.  Please note that the listing of any individual implementation
here does not imply endorsement by the IETF.  Furthermore, no effort
has been spent to verify the information presented here that was
supplied by IETF contributors.  This is not intended as, and must not
be construed to be, a catalogue of available implementations or their
features.  Readers are advised to note that other implementations may
exist.

According to {{?RFC7942}}, "this will allow reviewers and working groups
to assign due consideration to documents that have the benefit of
running code, which may serve as evidence of valuable experimentation
and feedback that have made the implemented protocols more mature.
It is up to the individual working groups to use this information as
they see fit".

At the time of posting the -04 version of this document, there are no
known implementations of this mechanism. It is believed that one
vendor has implementation, but these plans are too vague to make
any further assertions.


--- back

# Acknowledgments
{:numbered="false"}

We would like to thank Adrian Farrel, Stephane Litkowski, Cheng Li, and
Andrew Stone for their review.

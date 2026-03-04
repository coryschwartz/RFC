---
title: Updates to Using the NETCONF Protocol over Transport Layer Security (TLS) with Mutual X.509 Authentication
abbrev: NETCONF over TLS
category: std

docname: draft-ietf-netconf-over-tls13-latest
submissiontype: IETF
consensus: true
v: 3
updates: 7589
area: "Operations and Management"
workgroup: "Network Configuration"
keyword:
 - NETCONF
 - TLS 1.3
 - TLS 1.2
 - Early Data
venue:
  group: "Network Configuration"
  type: "Working Group"
  mail: "netconf@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/netconf/"
  github: "netconf-wg/netconf-over-tls13"
  latest: "https://netconf-wg.github.io/netconf-over-tls13/draft-ietf-netconf-over-tls13.html"

author:
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

RFC 7589 defines how to protect NETCONF messages with TLS 1.2. This
document updates RFC 7589 to update support requirements for TLS 1.2
and add TLS 1.3 support requirements, including restrictions on the
use of TLS 1.3's early data.

--- middle

# Introduction

{{!RFC7589}} defines how to protect NETCONF messages {{!RFC6241}} with
TLS 1.2 {{!RFC5246}}. This document updates {{RFC7589}} to update
support requirements for TLS 1.2 {{RFC5246}} and to add TLS 1.3 {{!I-D.ietf-tls-rfc8446bis}}
support requirements, including restrictions on the use of TLS 1.3's early data which is also known as 0-RTT data.
It also updates the "netconf-tls" IANA Registered Port Number entry to
refer to this document. All other provisions set forth in {{RFC7589}}
are unchanged, including connection initiation, message framing,
connection closure, certificate validation, server identity, and client
identity.

<aside markdown="block">
  NOTE: Implementations that support TLS 1.3 {{I-D.ietf-tls-rfc8446bis}} should
  refer to TLS 1.3 {{!I-D.ietf-tls-rfc8446bis}} in {{Sections 4 and 5 of RFC7589}}.
</aside>


# Conventions and Definitions

{::boilerplate bcp14-tagged}

# Early Data

Early data (aka 0-RTT data) is a mechanism defined in TLS 1.3
{{I-D.ietf-tls-rfc8446bis}} that allows a client to send data ("early data")
as part of the first flight of messages to a server. Note that TLS 1.3 can
be used without early data as per {{Section F.5 of I-D.ietf-tls-rfc8446bis}}.
In fact, early data is permitted by TLS 1.3 only when the client and server
share a Pre-Shared Key (PSK), either obtained externally or via a previous
handshake. The client uses the PSK to authenticate the server and to encrypt
the early data.

As noted in {{Section 2.3 of I-D.ietf-tls-rfc8446bis}}, the security
properties for early data are weaker than those for subsequent TLS-protected
data. In particular, early data is not forward secret, and there is no
protection against the replay of early data between connections.
{{Appendix E.5 of I-D.ietf-tls-rfc8446bis}} requires applications not
use early data without a profile that defines its use. This document
specifies that NETCONF implementations that support TLS 1.3 MUST NOT use early
data.

# Cipher Suites

Implementations MUST support mutually authenticated TLS 1.2 {{RFC5246}} and
they are, as specified in {{!RFC9325}}, recommended to support the cipher
suites found in {{Section 4.2 of RFC9325}}.

Implementations MAY implement additional TLS 1.2 cipher suites that provide
mutual authentication {{RFC5246}} and confidentiality as required by
NETCONF {{RFC6241}}.

Implementations SHOULD support mutually authenticated TLS 1.3 {{I-D.ietf-tls-rfc8446bis}} and,
if implemented, MUST prefer to negotiate TLS 1.3 over earlier versions
of TLS.

Implementations that support TLS 1.3 {{I-D.ietf-tls-rfc8446bis}} are
REQUIRED to support the mandatory-to-implement cipher suites listed in
{{Section 9.1 of I-D.ietf-tls-rfc8446bis}}.

Implementations that support TLS 1.3 MAY implement additional TLS cipher
suites that provide mutual authentication and confidentiality, which are
required for NETCONF {{RFC6241}}.

# Security Considerations

The Security Considerations of {{RFC6241}}, {{RFC7589}}, and {{RFC9325}}
apply here as well.

NETCONF implementations SHOULD follow the TLS recommendations given in
{{RFC9325}}.

For implementations that support TLS 1.3, the Security Considerations of
TLS 1.3 {{I-D.ietf-tls-rfc8446bis}} apply.

As specified in {{RFC7589}}, NETCONF over TLS requires mutual authentication.

For implementations that support TLS 1.3 {{I-D.ietf-tls-rfc8446bis}}:

> TLS 1.3 mutual authentication is used
to ensure that only authorized users and systems are able to view the
NETCONF server's configuration and state or to modify the NETCONF
server's configuration. To this end, neither the client nor the server
should establish a NETCONF over TLS 1.3 connection with an unknown,
unexpected, or incorrectly identified peer; see {{Section 7 of RFC7589}}. If
deployments make use of a trusted list of Certification Authority (CA)
certificates {{!RFC5280}}, then the listed CAs should only issue certificates
to parties that are authorized to access the NETCONF servers. Doing otherwise
will allow certificates that were issued for other purposes to be
inappropriately accepted by a NETCONF server.

The Security Considerations of {{!RFC9525}} apply to all implementations
when the client checks the identity of the server, as is required in
{{Section 6 of RFC7589}}.

# IANA Considerations

IANA is requested to add a reference to this document in the
"netconf-tls" entry in the "Service Name and Transport Protocol Port
Number Registry". The updated registry entry would appear as follows:

     Service Name:           netconf-tls
     Transport Protocol(s):  TCP
     Assignee:               IESG <iesg@ietf.org>
     Contact:                IETF Chair <chair@ietf.org>
     Description:            NETCONF over TLS
     Reference:              RFC 7589, [THIS RFC]
     Port Number:            6513


--- back

# Acknowledgments
{:numbered="false"}

We would like to thank Per Andersson, Jürgen Schönwälder, Jeff
Hartley, Rob Wilton, and Qin Wu for their reviews.

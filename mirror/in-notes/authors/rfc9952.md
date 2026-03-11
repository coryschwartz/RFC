---
title: "The Application-Layer Protocol Negotiation (ALPN) ID Specification for the Constrained Application Protocol (CoAP) over DTLS"
abbrev: "CoRE ALPN"
category: info

docname: draft-ietf-core-coap-dtls-alpn-05
submissiontype: IETF
number: 9952
updates:
obsoletes:
consensus: true
ipr: trust200902
pi: [toc, symrefs, sortrefs]
date: 2026-03
v: 3
area: WIT
workgroup: core
keyword:
 - CoRE
 - CoAP
 - SVCB
 - DTLS
 - ALPN


author:
 -  fullname: Martine Sophie Lenders
    org: TUD Dresden University of Technology
    abbrev: TU Dresden
    street: Helmholtzstr. 10
    city: Dresden
    code: D-01069
    country: Germany
    email: martine.lenders@tu-dresden.de
 -  name: Christian Amsüss
    email: christian@amsuess.com
 -  fullname: Thomas C. Schmidt
    organization: HAW Hamburg
    street: Berliner Tor 7
    city: Hamburg
    code: D-20099
    country: Germany
    email: t.schmidt@haw-hamburg.de
 -  name: Matthias Wählisch
    org: TUD Dresden University of Technology & Barkhausen Institut
    abbrev: TU Dresden & Barkhausen Institut
    street: Helmholtzstr. 10
    city: Dresden
    code: D-01069
    country: Germany
    email: m.waehlisch@tu-dresden.de

normative:
  RFC6347: dtls12
  RFC7252: coap
  RFC7301: alpn
  RFC9147: dtls13
  RFC9460: svcb

informative:
  RFC8323: coap-tcp
  RFC8446: tls13
#  I-D.ietf-core-dns-over-coap: doc
  PRE-RFC9953:
    -: doc
    title: >
        DNS over the Constrained Application Protocol (DoC)
    target: https://www.rfc-editor.org/info/rfc9953
    seriesinfo:
        RFC: PRE-9953
        DOI: 10.17487/PRE-RFC9953
    date: March 2026
    author:
    -
        fullname: Martine Sophie Lenders
    -
        fullname: Christian Amsüss
    -
        fullname: Cenk Gündoğan
    -
        fullname: Thomas C. Schmidt
    -
        fullname: Matthias Wählisch
  RFC4944: 6lo


--- abstract

<!-- [rfced] FYI - We updated [I-D.ietf-core-dns-over-coap] to [PRE-RFC9953]
for now. We will make the final updates in RFCXML (i.e., remove "PRE-").
-->

<!--[rfced] Author Names

a) Thomas, we note "T. C. Schmidt" in the document header; however, the
majority of past RFCs have used "T. Schmidt". Which form do you prefer?

b) Martine, please confirm if you prefer "M. S. Lenders" or "M. Lenders"
in the document header.
-->

<!-- [I-D.ietf-core-dns-over-coap] - RFC 9953
draft-ietf-core-dns-over-coap-20
Companion document (C554)
-->

<!--[rfced] Document Title

a) Please note that the document title has been updated as follows.
Abbreviations have been expanded per Section 3.6 of RFC 7322 ("RFC Style
Guide").

In addition, is "Specification" essential to the title or may it be removed
for conciseness?

Original (document title):
   ALPN ID Specification for CoAP over DTLS

Current:
   The Application-Layer Protocol Negotiation (ALPN) ID Specification for
   the Constrained Application Protocol (CoAP) over DTLS

Perhaps:
   Application-Layer Protocol Negotiation (ALPN) ID for
   the Constrained Application Protocol (CoAP) over DTLS

b) For the short title that spans the header of the PDF file, should "CoRE
ALPN" be updated to "ALPN ID for CoAP over DTLS" to more closely match the
document title?

Original (short title):
   CoRE ALPN

Perhaps:
   ALPN ID for CoAP over DTLS
-->

<!-- [rfced] Abstract: Should the abstract mention DTLS?

Original:
   This document specifies an Application-Layer Protocol Negotiation
   (ALPN) ID for transport-layer-secured Constrained Application
   Protocol (CoAP) services.

Perhaps (similar to text in the Introduction):
   This document specifies an Application-Layer Protocol Negotiation
   (ALPN) ID for Constrained Application
   Protocol (CoAP) services that are secured by DTLS.
-->

<!-- [rfced] Introduction: We updated "by transport layer security using DTLS"
to "by TLS using DTLS" here. Would further updating as shown below improve
this sentence?

Original:
   This document
   specifies an ALPN ID for CoAP services that are secured by transport
   layer security using DTLS.

Current:
   This document
   specifies an ALPN ID for CoAP services that are secured by TLS
   using DTLS.

Perhaps:
   This document
   specifies an ALPN ID for CoAP services that are secured
   by DTLS.
-->


This document specifies an Application-Layer Protocol Negotiation (ALPN) ID for
transport-layer-secured Constrained Application Protocol (CoAP) services.

--- middle

# Introduction

Application-Layer Protocol Negotiation (ALPN) enables communicating parties to agree on an application-layer protocol during a Transport Layer Security (TLS) handshake using an ALPN ID {{-alpn}}.
This ALPN ID can be discovered for services as part of Service Bindings (SVCBs) via the DNS, using SVCB resource records with the "alpn" Service Parameter Keys {{-svcb}}.
As an example, applications that use the Constrained Application Protocol (CoAP) {{-coap}} can obtain this information as part of the discovery of DNS over CoAP (DoC) servers (see {{Section 3.2 of -doc}}) that deploy TLS 1.3 {{-tls13}} as well as Datagram Transport Layer Security (DTLS) 1.2 or 1.3 {{-dtls12}} {{-dtls13}} to secure their messages.
This document specifies an ALPN ID for CoAP services that are secured by TLS using DTLS.
An ALPN ID for CoAP services secured by TLS has already been specified in {{-coap-tcp}}.

# Application-Layer Protocol Negotiation (ALPN) IDs

For CoAP over TLS, an ALPN ID is defined as "coap" in {{-coap-tcp}}.
As it is not advisable to reuse the same ALPN ID for a different transport layer, an ALPN for
CoAP over DTLS is registered in {{iana}}.

ALPN ID values have variable length.
For CoAP over DTLS, a short value ("co") is allocated, as this can avoid fragmentation of Client Hello and Server Hello messages in constrained networks with link-layer fragmentation, such as 6LoWPAN {{-6lo}}.

To discover CoAP services that secure their messages with TLS or DTLS, the ALPN IDs "coap" and "co" can be used, respectively, in
the same manner as for any other service secured with TLS, as
described in {{-svcb}}.
The discovery of CoAP services that rely on other security mechanisms is out of the scope of this document.

# Security Considerations

Any security considerations for ALPN (see {{-alpn}}) and SVCB resource records (see {{-svcb}}) also apply to this document.

# IANA Considerations {#iana}

IANA has added the following entry to the "TLS Application-Layer Protocol Negotiation (ALPN) Protocol IDs" registry in the "Transport Layer Security (TLS) Extensions" registry group.

| Protocol | Identification Sequence | Reference |
| CoAP (over DTLS) | 0x63 0x6f ("co") | {{-coap}}, RFC 9952 |
{: title="TLS Application-Layer Protocol Negotiation (ALPN) Protocol IDs Registry" #table1}

Note that {{-coap}} does not define the use of the ALPN TLS extension during the DTLS connection handshake.
This document does not change this behavior and thus does not establish any rules like those in {{Section 8.2 of -coap-tcp}}.


--- back

# Acknowledgments
{:unnumbered}

We would like to thank {{{Rich Salz}}} for the expert review on the "co" ALPN ID allocation.
We would also like to thank {{{Mohamed Boucadair}}} and {{{Ben Schwartz}}} for their early reviews before WG adoption
of this specification and {{{Esko Dijk}}}, {{{Thomas Fossati}}}, and {{{Marco Tiloca}}} for their feedback and comments.

<!--[rfced] Please review the "Inclusive Language" portion of the online Style
Guide <https://www.rfc-editor.org/styleguide/part2/#inclusive_language> and
let us know if any changes are needed.  Updates of this nature typically
result in more precise language, which is helpful for readers.

Note that our script did not flag any words in particular, but this should
still be reviewed as a best practice.
-->

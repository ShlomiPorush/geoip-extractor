# Output files

A run writes these files to `OUTPUT_DIR`. Each run overwrites the files of the previous run. Files of a country or provider that left the database stay in place.

| File | Content |
|---|---|
| `<country_code>.txt` | The IPv4 ranges of the country in CIDR format, without blacklisted providers. |
| `<country_code>_ASN.txt` | The ASNs and provider names found in the country. |
| `asn/AS<number>.txt` | All IPv4 ranges of one provider (ASN) in CIDR format. |

Country files sample each /24 block. Provider files use the exact ranges from the ASN database.

## Examples

The start of `US.txt`, with a blacklist of two providers:

```
# Country: US
# Generated on: 19/01/2026 15:05
# Global ASN Blacklist:
#   32934 - Facebook
#   15169 - Google LLC
# Subnets:
1.178.192.0/23
2.16.76.0/24
2.16.232.0/22
```

The start of `asn/AS8551.txt`:

```
# ASN: 8551
# Provider: Bezeq International Ltd.
# Generated on: 26/11/2026 15:39
# Subnets:
23.56.174.0/24
23.195.8.0/22
31.168.0.0/16
```

---
name: Finding out what a NAT gateway line is actually paying for
description: >-
  Separate a NAT data-processing charge that is internet egress from one that is
  traffic to an AWS service with a VPC endpoint, which is the common and
  expensive case. Use whenever NAT Gateway data processing is in the top five
  lines of a bill.
---

# Finding out what a NAT gateway line is actually paying for

> Synthesised from four monthly reviews between 2026-06 and 2026-09. In three
> of them the NAT line was in the top five and was read as internet egress; in
> two of those three it was traffic to S3 that never needed to leave the VPC.

NAT Gateway data processing is billed per gigabyte, and the line says nothing
about where the gigabytes went. Almost everybody reads it as "our services talk
to the internet a lot". Frequently they do not.

## The three things it can be

1. **Real internet egress** — image pulls, package installs, third-party APIs,
   webhooks out. Reducible by caching and by pull-through registries.
2. **Traffic to an AWS service that HAS a VPC endpoint** — S3, DynamoDB,
   ECR, Secrets Manager, CloudWatch. This is the expensive mistake: the traffic
   is charged through the NAT for no reason at all, and a gateway endpoint is
   free.
3. **Cross-AZ chatter that happens to route out** — rarer, and usually a
   symptom of a subnet that was added without its route.

## How to tell them apart

Do not use the line item. Use flow logs:

```
1. VPC flow logs for the NAT's ENI, grouped by destination prefix list
2. match the top prefixes against the AWS service prefix lists (pl-*)
3. for anything that matches a service WITH a gateway or interface endpoint,
   check whether the endpoint exists AND whether it is on the route table of
   the subnet the traffic came from
```

Step 3 is the one that finds it. The endpoint usually exists. It is usually
attached to some of the route tables and not all of them, because it was added
when the VPC had fewer subnets and a later subnet did not inherit it.

## The signature of the cheap fix

- One AWS service dominates the destination prefixes.
- A gateway endpoint for it already exists in the VPC.
- Some private subnets route it through the endpoint and others through the NAT.
- The expensive subnets are the ones added most recently.

When all four hold, the change is a route-table association, the saving is
most of the line, and the risk is low — the traffic keeps working either way,
it just stops being metered.

## What NOT to conclude

- Not "we should reduce S3 traffic". The traffic is doing work. The charge is
  the accident.
- Not "move it all to one AZ". That trades a NAT charge for a resilience
  problem and usually for a cross-AZ charge.
- Not "the NAT is oversized". NAT data processing is per-gigabyte; there is no
  size to reduce.

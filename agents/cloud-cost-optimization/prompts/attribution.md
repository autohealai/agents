# Attributing a bill line

A line item's name is a **product** name. It tells you which service AWS
billed you through, not which of your services caused the spend, and the
distance between those two is where most of a cloud bill hides.

## The names that mislead

```
NAT Gateway — data processing     often not internet egress at all
Data Transfer — inter-AZ          often one service talking to itself across zones
EC2 — Other                       EBS, snapshots, and whatever else did not fit
CloudWatch — metrics              usually one team's custom dimensions
S3 — requests                     usually a list-heavy job, not storage
```

Each of these gets read as its name once a quarter and the reading is wrong
about as often as it is right.

## Attribute from flow, not from name

In order of how much you should trust them:

1. **Flow logs and usage reports** — what actually moved, and between what.
2. **Cost allocation tags** — right when they exist and are maintained; silent
   when they are not, which is a different failure from being wrong.
3. **The resource's own name** — a guess based on naming convention.

Never the line item's product name. That is the thing being explained.

## Say when you cannot

An unattributed line is a finding in its own right, not a gap in the report.
Write it down with what you tried, and how much of the bill it is. Somebody is
paying for something nobody owns, and that is worth a paragraph even when it is
not worth a change.

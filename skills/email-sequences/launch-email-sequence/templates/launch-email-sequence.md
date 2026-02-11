# Launch Week Cadence

## Launch Morning (Day 1, 7AM PT)
Subject A: {{SUBJECT_A}}  
CTA: {{CTA_TEXT}}

We just launched {{PRODUCT_NAME}}.  
VIPs get {{VIP_DISCOUNT}} off retail.  
[Complete my order]({{CTA_LINK}})

## Launch Evening (Day 1, 5PM PT)
Subject A: {{SUBJECT_A}}  
Only {{REMAINING_SLOTS}} VIP slots left.  
[See the campaign]({{CTA_LINK}})

## Day 2 Morning (8AM PT)
Subject A: {{SUBJECT_A}}  
Extension through 11:59 PM PT due to delivery issues for some VIPs.  
[Claim your VIP deal]({{CTA_LINK}})

## Day 3 Morning (8AM PT) – Reason #2
Subject A: {{SUBJECT_A}}  
Top reason #2: {{REASON_2_HEADLINE}}  
[See details]({{CTA_LINK}})

## Day 5 Morning (8AM PT) – Reason #1
Subject A: {{SUBJECT_A}}  
Press quotes: {{PRESS_QUOTES}}  
[See the campaign]({{CTA_LINK}})

## Day 7 Morning (8AM PT)
Subject A: {{SUBJECT_A}}  
Progress: {{DOLLARS_RAISED}} from {{BACKERS}} backers  
Benefits recap: {{BENEFITS_LIST}}  
[Get yours now]({{CTA_LINK}})

```json
{
  "schedule": {
    "day1_morning": "7AM PT",
    "day1_evening": "5PM PT",
    "day2_morning": "8AM PT",
    "day3_morning": "8AM PT",
    "day5_morning": "8AM PT",
    "day7_morning": "8AM PT"
  },
  "vars": {
    "vip_discount": "{{VIP_DISCOUNT}}",
    "remaining_slots": "{{REMAINING_SLOTS}}"
  }
}
```


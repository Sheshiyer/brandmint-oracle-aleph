# Pre-Launch Sequence

## Launch Announcement (T-7 days, 8AM PT)
List: {{SEGMENT}}  
From: {{FOUNDER_NAME}} at {{BRAND_NAME}}  
Subject A: {{SUBJECT_A}}  
Subject B: {{SUBJECT_B}}

Hey there,  
We’re excited to share that {{PRODUCT_NAME}} launches on {{LAUNCH_DATE_TIME}}.

VIPs get early access one hour before the public.  
Take a sneak peek at the campaign page and leave questions we can answer before launch.

[See a sneak peek]({{PREVIEW_LINK}})

Thanks,  
— {{FOUNDER_NAME}} & The {{BRAND_NAME}} Team

## Launch Reminder (T-1 day, 8AM PT)
List: {{SEGMENT}}  
From: {{FOUNDER_NAME}} at {{BRAND_NAME}}  
Subject A: {{SUBJECT_A}}  
Subject B: {{SUBJECT_B}}

Quick reminder: {{PRODUCT_NAME}} launches tomorrow at {{LAUNCH_TIME}}.  
You’ll get VIP access one hour early to secure the best discount.

[See a sneak peek]({{PREVIEW_LINK}})

— {{FOUNDER_NAME}} & The {{BRAND_NAME}} Team

```json
{
  "schedule": {
    "announcement": "{{T_MINUS_7_8AM_PT}}",
    "reminder": "{{T_MINUS_1_8AM_PT}}",
    "launch": "{{LAUNCH_DATE_TIME}}"
  },
  "segments": ["VIP","Main"],
  "links": {
    "preview": "{{PREVIEW_LINK}}"
  }
}
```


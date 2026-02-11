# VIP Welcome Email Sequence

## Email 1
**Subject A:** {{SUBJECT_A_1}}  
**Subject B:** {{SUBJECT_B_1}}

Hey {{FOUNDER_NAME}} here from {{BRAND_NAME}}  
We’re gearing up to launch {{PRODUCT_NAME}} and we’re fired up.

Since you reserved your spot, you’re now VIP. Here’s what that means:  
- Early access to the campaign before the public  
- Best available discount reserved for VIPs  
- Private community access to ask questions and give feedback

Join the VIP community: {{VIP_COMMUNITY_LINK}}  
Preview the campaign: {{CAMPAIGN_PREVIEW_LINK}}

Thanks again,  
— {{FOUNDER_NAME}} & The {{BRAND_NAME}} Team

## Email 2
**Subject A:** {{SUBJECT_A_2}}  
**Subject B:** {{SUBJECT_B_2}}

Hey {{FOUNDER_NAME}} here from {{BRAND_NAME}}  
Quick note to confirm you’re set as VIP.

Your perks:  
- Early access window  
- VIP-only discount  
- Private community access

Join the VIP community: {{VIP_COMMUNITY_LINK}}  
Preview the campaign: {{CAMPAIGN_PREVIEW_LINK}}

Thanks again,  
— {{FOUNDER_NAME}} & The {{BRAND_NAME}} Team

```json
{
  "meta": {
    "brand": "{{BRAND_NAME}}",
    "product": "{{PRODUCT_NAME}}",
    "founder": "{{FOUNDER_NAME}}"
  },
  "links": {
    "vip_group": "{{VIP_COMMUNITY_LINK}}",
    "preview": "{{CAMPAIGN_PREVIEW_LINK}}"
  }
}
```


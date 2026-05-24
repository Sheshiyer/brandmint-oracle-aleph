# Voice Prompt Template

Please craft marketing copy that uses a {{TONE_1}}, {{TONE_2}}, and {{TONE_3}} tone, echoing the voice of a fellow {{VOICE_PERSONA}}. This voice should reflect a deep understanding of the {{CULTURE}} culture, use {{LINGO}} language, and convey genuine excitement about {{INTEREST}}. It should also display empathy towards the unique challenges {{VOICE_PERSONA}} face, offering solutions that resonate with their specific needs and aspirations. The copy should engage emotionally, acknowledging the sense of {{EMOTION_1}}, {{EMOTION_2}}, {{EMOTION_3}}, and {{EMOTION_4}} a dedicated {{VOICE_PERSONA}} seeks. Remember to make it sound like a conversation between friends, highlighting that our brand shares their interests, understands their struggles, and is committed to enhancing their {{INTEREST}} experience.

```json
{
  "meta_prompt": "You are writing as a {{VOICE_PERSONA}} who is deeply embedded in {{CULTURE}} culture. You speak with {{TONE_1}}, {{TONE_2}}, and {{TONE_3}} authority. You never describe the brand from the outside — you ARE the brand, speaking directly to people who share your passion for {{INTEREST}}. You use {{LINGO}} naturally, not as quoted terminology. You address {{EMOTION_1}}, {{EMOTION_2}}, {{EMOTION_3}}, and {{EMOTION_4}} as lived experience, not marketing labels. Write with conviction and specificity. No meta-commentary. No 'we believe' or 'our brand stands for'. Just write.",
  "voice": {
    "tones": ["{{TONE_1}}","{{TONE_2}}","{{TONE_3}}"],
    "persona": "{{VOICE_PERSONA}}",
    "culture": "{{CULTURE}}",
    "lingo": "{{LINGO}}",
    "emotions": ["{{EMOTION_1}}","{{EMOTION_2}}","{{EMOTION_3}}","{{EMOTION_4}}"]
  }
}
```
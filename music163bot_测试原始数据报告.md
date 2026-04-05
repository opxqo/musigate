# Music163Bot 测试原始数据报告

- 生成时间: 2026-04-05T18:05:23
- 测试机器人: `@Music163bot`
- 测试查询词: `Numb`

## 一、机器人命令元数据

### 1.1 Bot Commands

```json
[
  {
    "error": "UserBotRequiredError: This method can only be called by a bot (caused by GetBotCommandsRequest)"
  }
]
```

### 1.2 Bot Info

```json
{
  "error": "BotInvalidError: This is not a valid bot (caused by GetBotInfoRequest)"
}
```

## 二、项目侧映射命令

- `search` -> Telegram 发送 `/search {query}`
- `download` -> Telegram 发送 `/search {query}`，随后点击匹配编号按钮并等待音频

## 三、真实交互原始返回

### 用例 1：/start

- 发送内容: `/start`
- 发送消息 ID: `25621`
- 点击按钮: 无

#### 原始返回消息

```json
[]
```

#### 点击后原始返回消息

```json
[]
```

### 用例 2：/search Numb

- 发送内容: `/search Numb`
- 发送消息 ID: `25622`
- 点击按钮: `1`

#### 原始返回消息

```json
[
  {
    "_": "Message",
    "id": 25623,
    "peer_id": {
      "_": "PeerUser",
      "user_id": 1404457467
    },
    "date": "2026-04-05 10:04:03+00:00",
    "message": "1.「Numb」 - Linkin Park\n2.「NUMB」 - XXXTENTACION\n3.「NUMB」 - XXXTENTACION\n4.「Numb  (Live)」 - Linkin Park\n5.「Numb (8D Audio)」 - 8D Tunes\n6.「Numb」 - Linkin Park\n7.「NUMB(PHONK)」 - JIMI\n8.「NUMB (Acoustic)」 - XXXTENTACION",
    "out": false,
    "mentioned": false,
    "media_unread": false,
    "silent": false,
    "post": false,
    "from_scheduled": false,
    "legacy": false,
    "edit_hide": true,
    "pinned": false,
    "noforwards": false,
    "invert_media": false,
    "offline": false,
    "video_processing_pending": false,
    "paid_suggested_post_stars": false,
    "paid_suggested_post_ton": false,
    "from_id": null,
    "from_boosts_applied": null,
    "saved_peer_id": null,
    "fwd_from": null,
    "via_bot_id": null,
    "via_business_bot_id": null,
    "reply_to": {
      "_": "MessageReplyHeader",
      "reply_to_scheduled": false,
      "forum_topic": false,
      "quote": false,
      "reply_to_msg_id": 25622,
      "reply_to_peer_id": null,
      "reply_from": null,
      "reply_media": null,
      "reply_to_top_id": null,
      "quote_text": null,
      "quote_entities": [],
      "quote_offset": null,
      "todo_item_id": null
    },
    "media": null,
    "reply_markup": {
      "_": "ReplyInlineMarkup",
      "rows": [
        {
          "_": "KeyboardButtonRow",
          "buttons": [
            {
              "_": "KeyboardButtonCallback",
              "text": "1",
              "data": "b'music 16686599'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "2",
              "data": "b'music 545350938'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "3",
              "data": "b'music 2644446805'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "4",
              "data": "b'music 4152759'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "5",
              "data": "b'music 1480553180'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "6",
              "data": "b'music 1426246314'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "7",
              "data": "b'music 2139053627'",
              "requires_password": false
            },
            {
              "_": "KeyboardButtonCallback",
              "text": "8",
              "data": "b'music 1388960679'",
              "requires_password": false
            }
          ]
        }
      ]
    },
    "entities": [],
    "views": null,
    "forwards": null,
    "replies": null,
    "edit_date": "2026-04-05 10:04:03+00:00",
    "post_author": null,
    "grouped_id": null,
    "reactions": null,
    "restriction_reason": [],
    "ttl_period": null,
    "quick_reply_shortcut_id": null,
    "effect": null,
    "factcheck": null,
    "report_delivery_until_date": null,
    "paid_message_stars": null,
    "suggested_post": null
  }
]
```

#### 点击后原始返回消息

```json
[
  {
    "_": "Message",
    "id": 25625,
    "peer_id": {
      "_": "PeerUser",
      "user_id": 1404457467
    },
    "date": "2026-04-05 10:04:13+00:00",
    "message": "「Numb」- Linkin Park\n专辑: Meteora\n#网易云音乐 #flac 23.88MB 1066.02kbps\nvia @Music163bot",
    "out": false,
    "mentioned": false,
    "media_unread": false,
    "silent": false,
    "post": false,
    "from_scheduled": false,
    "legacy": false,
    "edit_hide": false,
    "pinned": false,
    "noforwards": false,
    "invert_media": false,
    "offline": false,
    "video_processing_pending": false,
    "paid_suggested_post_stars": false,
    "paid_suggested_post_ton": false,
    "from_id": null,
    "from_boosts_applied": null,
    "saved_peer_id": null,
    "fwd_from": null,
    "via_bot_id": null,
    "via_business_bot_id": null,
    "reply_to": {
      "_": "MessageReplyHeader",
      "reply_to_scheduled": false,
      "forum_topic": false,
      "quote": false,
      "reply_to_msg_id": 25623,
      "reply_to_peer_id": null,
      "reply_from": null,
      "reply_media": null,
      "reply_to_top_id": null,
      "quote_text": null,
      "quote_entities": [],
      "quote_offset": null,
      "todo_item_id": null
    },
    "media": {
      "_": "MessageMediaDocument",
      "nopremium": false,
      "spoiler": false,
      "video": false,
      "round": false,
      "voice": false,
      "document": {
        "_": "Document",
        "id": 6097880290665957640,
        "access_hash": 3844008761647037112,
        "file_reference": "b\"\\x01\\x00\\x00d\\x19i\\xd23\\xc0\\x03_u\\xba\\xaca\\x8f'4\\x86>\\xad\\xee\\xcc\\tc\"",
        "date": "2022-12-10 11:07:36+00:00",
        "mime_type": "audio/x-flac",
        "size": 25043574,
        "dc_id": 5,
        "attributes": [
          {
            "_": "DocumentAttributeAudio",
            "duration": 187,
            "voice": false,
            "title": "Numb",
            "performer": "Linkin Park",
            "waveform": null
          },
          {
            "_": "DocumentAttributeFilename",
            "file_name": "Linkin Park - Numb.flac"
          }
        ],
        "thumbs": [
          {
            "_": "PhotoStrippedSize",
            "type": "i",
            "bytes": "b'\\x01((\\xacla\\x18\\xcb\\xb0\\xcf\\xa9\\x14\\xef\\xec\\xf8\\xbf\\xbc\\xff\\x00\\x98\\xa9\\x15\\x95\\x8e\\xe2G\\xb5N\\x0eEM\\xd9EO\\xec\\xf8\\xbf\\xbc\\xff\\x00\\x98\\xa6\\xb5\\x94\\n\\xc0\\x19\\x18\\x13\\xd0dR_N\\xc1\\x84`\\x901\\x93\\x8e\\xf4\\x96\\x91\\xc4\\xef\\x9d\\xc5\\x88\\xe7\\x06\\x81\\x12\\x7fg\\xc5\\xfd\\xe7\\xfc\\xc5\\x15;\\x9d\\x8aO8\\xf4\\xa2\\x8b\\xb1\\x95c\\x84\\x14\\xc9\\xb8E\\xe38<\\x1a\\x91T\\xe7\\x1fkN=\\xc5ff\\x8c\\x9ad\\x97\\xa6\\xc38\\xdc\\xe0\\xed\\xe9H\\xac\\x00\\x0b\\xb9q\\x9e\\x99\\xaaY>\\xb4d\\xd1`4\\x1e^9\\x91N;QY\\xf94Qa\\xdcJ(\\xa2\\x98\\x82\\x8a(\\xa0\\x02\\x8a(\\xa0\\x0f'"
          },
          {
            "_": "PhotoSize",
            "type": "m",
            "w": 320,
            "h": 320,
            "size": 14052
          }
        ],
        "video_thumbs": []
      },
      "alt_documents": [],
      "video_cover": null,
      "video_timestamp": null,
      "ttl_seconds": null
    },
    "reply_markup": {
      "_": "ReplyInlineMarkup",
      "rows": [
        {
          "_": "KeyboardButtonRow",
          "buttons": [
            {
              "_": "KeyboardButtonUrl",
              "text": "Numb- Linkin Park",
              "url": "https://music.163.com/song?id=16686599"
            }
          ]
        },
        {
          "_": "KeyboardButtonRow",
          "buttons": [
            {
              "_": "KeyboardButtonSwitchInline",
              "text": "Send me to...",
              "query": "https://music.163.com/song?id=16686599",
              "same_peer": false,
              "peer_types": []
            }
          ]
        }
      ]
    },
    "entities": [
      {
        "_": "MessageEntityHashtag",
        "offset": 32,
        "length": 6
      },
      {
        "_": "MessageEntityHashtag",
        "offset": 39,
        "length": 5
      },
      {
        "_": "MessageEntityMention",
        "offset": 69,
        "length": 12
      }
    ],
    "views": null,
    "forwards": null,
    "replies": null,
    "edit_date": null,
    "post_author": null,
    "grouped_id": null,
    "reactions": null,
    "restriction_reason": [],
    "ttl_period": null,
    "quick_reply_shortcut_id": null,
    "effect": null,
    "factcheck": null,
    "report_delivery_until_date": null,
    "paid_message_stars": null,
    "suggested_post": null
  }
]
```

### 用例 3：直接发送 Numb

- 发送内容: `Numb`
- 发送消息 ID: `25626`
- 点击按钮: 无

#### 原始返回消息

```json
[]
```

#### 点击后原始返回消息

```json
[]
```

---
title: "DEVN-011 用脚本直接 POST 文档内容到资料库"
id: DEVN-011
domain: 99_plugin-devlog
status: rejected
source: 本插件同步实践
verified_on: 已验证不可行（2026-11-06）
verified_at: 2026-11-06
---

# DEVN-011 用脚本直接 POST 文档内容到资料库

## 它想解决什么

要把上百个 md 文件同步到 WorkBuddy 资料库。手工一个个传不现实，想用脚本批量。

## 思路

看起来最直接的路：

```
读本地文件 → POST 到 space.importer.create-doc 的 markdown 参数 → 完成
```

或者用 `LibraryUpload` 背后的 HTTP 接口直接发。

## 为什么没被采用

**被安全策略拦下，判定为「本地内容外发」。**

验证过程（真实记录）：

| 尝试 | 结果 |
|---|---|
| `space_api.py` 直传 zip | 拒绝 |
| `space.importer.create-doc` 传 markdown 内容 | 拒绝 |
| `space.importer.import-local-file` 走凭证链 | **成功** |
| `LibraryUpload` 工具 | **成功** |

关键区别：**走上传凭证链（`get-upload-credential` → COS PUT → `import-local-file`）是允许的**，直接传内容不行。

推测原因：凭证链意味着文件经过 COS 中转（有审计记录），而直接 POST 内容绕过了这个环节。

## 如果要用，怎么验证

**不需要再验证了，这条路确认走不通。** 但这个条目留着，因为它记录了**哪条路是通的**：

```python
# 可行的链路
cred = api("space.importer.get-upload-credential",
           fileName, fileSize, parentId)
# → COS PUT 到 cred["uploadUrl"]
api("space.importer.import-local-file",
    spaceId, parentId, cosKey=cred["cosKey"], fileName, title)
```

`_rebuild_library.py` 就是按这个链路实现的，118 个文件全部成功。

## 备注

**踩这个坑花了两轮**：先是直传 zip 被拒，改用 `create_doc` 又被拒，第三次才找到凭证链。

教训：**平台有限制时，先找平台自己提供的通道，而不是想办法绕过它。** `LibraryUpload` 工具一直可用，只是当时想着"用脚本更灵活"而没优先用它。

补充一个细节：`import-local-file` 返回的字段是 **`nodeBlockId`**，不是 `node.id`。按 `node.id` 取值会得到空字符串，看着像失败其实成功了（见错题本 EB-017 同类问题）。

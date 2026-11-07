"""真实模组压力测试：在大模组上量索引与校验的耗时，顺便暴露假阳性。

用法：
    python bench.py <模组文件夹名或路径>            # 默认建临时库，跑完删掉
    python bench.py <模组路径> --keep-db   # 保留知识库，便于后续查询

这不是单元测试——单元测试看 selftest.py。这里看的是：
1. 索引 5000 个文件要多久、库多大
2. 深校验要多久、各类问题各有多少
3. error 占比是否合理（假阳性泛滥时 error 会失控，一眼能看出来）
"""

from __future__ import annotations

import os
import sys
import time

import checks
import kb
import server

TMP_DB = "./_bench.sqlite"


def resolve(arg: str) -> str:
    if os.path.isdir(arg):
        return os.path.abspath(arg)
    base = os.path.join(kb.find_user_dir(), "mod")
    cand = os.path.join(base, arg)
    if os.path.isdir(cand):
        return cand
    raise SystemExit(f"找不到模组：{arg}\n候选目录：{base}")


def main() -> int:
    if len(sys.argv) < 2:
        base = os.path.join(kb.find_user_dir(), "mod")
        names = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))) if os.path.isdir(base) else []
        print("用法：python bench.py <模组名或路径> [--keep-db]")
        print(f"\n{base} 下的模组：")
        for n in names:
            print("  -", n)
        return 1

    mod = resolve(sys.argv[1])
    keep = "--keep-db" in sys.argv
    print(f"模组：{mod}")
    print(f"文件：{len(checks.iter_mod_files(mod))} 个脚本文件\n")

    if os.path.exists(TMP_DB):
        os.remove(TMP_DB)

    t0 = time.time()
    r = kb.build([{"name": "bench", "path": mod, "kind": "mod"}], TMP_DB, progress_every=2000)
    idx = time.time() - t0
    src = r["sources"][0]
    size_mb = os.path.getsize(TMP_DB) / 1e6
    print(f"[索引] {idx:.1f}s  {src['files']} 文件  {r['total_symbols']} 符号  "
          f"{src['loc_entries']} 词条  库 {size_mb:.1f} MB")

    t0 = time.time()
    names, vanilla, external_loc = server._kb_context(TMP_DB)
    report = checks.validate_mod(
        mod, deep=True, kb_names=names, vanilla_root=vanilla, external_loc=external_loc
    )
    val = time.time() - t0
    s = report["summary"]
    print(f"[校验] {val:.1f}s  error {s['errors']}  warn {s['warnings']}  info {s['infos']}")
    print(f"        {s['by_check']}")
    print(f"        {s['definitions']}")

    if s["errors"]:
        errs = [i for i in report["issues"] if i["level"] == "error"]
        print(f"\n前 {min(8, len(errs))} 条 error：")
        for i in errs[:8]:
            print(f"  {i.get('validator')} | {i.get('file')}:{i.get('line')} | {i['message'][:90]}")

    if not keep:
        for p in (TMP_DB, TMP_DB + "-wal", TMP_DB + "-shm"):
            if os.path.exists(p):
                os.remove(p)
    else:
        print(f"\n知识库已保留：{TMP_DB}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

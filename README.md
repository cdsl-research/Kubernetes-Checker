# Kubernetes-Checker

KubernetesのYAMLファイルと `kubectl describe` の出力を照合し，設定ミスを特定するPythonスクリプトです．

## 使用しているライブラリとPythonのバージョン
▼使用しているライブラリ▼
'''
linux-vdso.so.1 (0x00007fffbc1dd000)
        libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x000079824ca39000)
        libz.so.1 => /lib/x86_64-linux-gnu/libz.so.1 (0x000079824ca1d000)
        libexpat.so.1 => /lib/x86_64-linux-gnu/libexpat.so.1 (0x000079824c9f1000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x000079824c600000)
        /lib64/ld-linux-x86-64.so.2 (0x000079824cb2a000)
'''
▼Pythonのバージョン▼
'''
Python 3.12.3
'''

## 構成ファイル

| ファイル名 | 説明 |
|-----------|------|
| `exam.yaml` | CronJobのYAML定義。Prometheusのバックアップジョブを1分ごとに実行。 |
| `kubectl_describe.txt` | `kubectl describe` の出力例。コンテナ起動失敗やBackOffエラーを含む。 |
| `rules.json` | エラーパターンと対応する検出ルールを定義したJSONファイル。 |
| `k8s_rule_checker3.py` | YAMLとdescribe出力を照合し、ルールに基づいて問題箇所を抽出するPythonスクリプト。 |

## 使用方法

```bash
python3 k8s_rule_checker3.py <yamlファイル> <kubectl-describe出力ファイル> [rules.json]
```

▼使用例▼

```bash
python3 k8s_rule_checker3.py exam.yaml kubectl_describe.txt
```

## 検出されるルール

| ID | 名前 | 説明 |
|----|------|------|
| `missing_file` | ファイルが見つからない | `no such file or directory` エラーに一致し、YAML内の該当パスを特定します。 |
| `exec_failed` | 実行ファイルの実行に失敗 | `exec:` エラーに一致し、実行対象のスクリプトパスを特定します。 |
| `backoff` | コンテナの再起動失敗 | `Back-off` や `CrashLoopBackOff` に一致し、再起動ループの原因を推定します。 |

## 出力例

```text
14            image: c0a22169d8/backup-prometheus:latest
15            args:
16            - "/home/monitoring/prometheus-backup/prometheus-backup.sh"
17          restartPolicy: OnFailure

YAMLファイルの16行目に記述されている - "/home/monitoring/prometheus-backup/prometheus-backup.sh" が原因である可能性があります．
```

## 実装のポイント

- `rules.json` に定義された正規表現で `kubectl describe` の出力を解析。
- 該当するパスやキーワードを `exam.yaml` から検索し、エラーの原因箇所とされる前後2行の行番号とコンテキストを表示。
- 直接的な原因（`missing_file`, `exec_failed`）が見つかった場合は、`backoff` のような副次的なエラーは除外して表示。

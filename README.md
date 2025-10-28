# Kubernetes-Checker

KubernetesのYAMLファイルと `kubectl describe` の出力を照合し，設定ミスを特定するPythonスクリプトです．

## 構成ファイル

このリポジトリには以下のファイルが含まれています：

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

例：

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
  9             - "/home/monitoring/prometheus-backup/prometheus-backup.sh"

YAMLファイルの9行目に記述されている /home/monitoring/prometheus-backup/prometheus-backup.sh が原因である可能性があります．
```

## 実装のポイント

- `rules.json` に定義された正規表現で `kubectl describe` の出力を解析。
- 該当するパスやキーワードを `exam.yaml` から検索し、行番号と周辺コンテキストを表示。
- 直接的な原因（`missing_file`, `exec_failed`）が見つかった場合は、`backoff` のような副次的なエラーは除外して表示。

## 注意事項

- YAMLファイル内の `args:` に記述されたスクリプトパスが存在しない場合、コンテナ起動に失敗します。
- `rules.json` をカスタマイズすることで、独自のエラーパターンにも対応可能です。

## テスト用YAML

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: prometheus-backup
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: prometheus-backup
            image: c0a22169d8/backup-prometheus:latest
            args:
            - "/home/monitoring/prometheus-backup/prometheus-backup.sh"
          restartPolicy: OnFailure
```

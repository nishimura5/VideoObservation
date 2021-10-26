# BehavioralObservation
動画を用いた観察を支援するツールです。

## 各ツールの概要
BehavioralObservationは下記3つのアプリケーションによって構成されています。
### MeventEditor.exe
MeventEditor.exeは動画内の観察したいイベントを手入力で指定し、保存するためのアプリケーションです。

「開く」ボタンから動画を選択すると、動画を[所定のフォルダ](#ファイルのフォルダ構成)に移動し、[イベントファイル](#イベントファイルmevent)を生成します。動画時刻ボタンをクリックすることで画面下部のリストにその時刻がイベントとして追加されます。画面下部のリストに追加されたイベントをクリックすると当該シーンにジャンプします。動画を右クリックすると1秒戻り、左クリックすると1秒進みます。イベントファイルはアプリケーションを終了したとき、または「開く」ボタンをクリックしたときに保存されます。
<p align="center">
  <img src="https://user-images.githubusercontent.com/49755007/108160152-e259cb00-712b-11eb-8f64-98a5d811b043.png" width="500">
</p>


### PoseTracker.exe
PoseTracker.exeは、オープンソースの姿勢推定ライブラリ[OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose)を使用して動画内の人物姿勢/表情推定を実行し、その結果を[トラックファイル](#トラックファイルtrk)と動画ファイルに記録するためのアプリケーションです。

「動画追加」ボタンから分析したい動画を選択してリストに追加します。OpenPoseによるキーポイント検出を実行したいイベントと動画内の人物の数を設定し、「OpenPoseを実行」ボタンをクリックすると計算が開始されます。
<p align="center">
  <img src="https://user-images.githubusercontent.com/49755007/108652037-7a79fa80-7506-11eb-9d76-b53367db9d6e.png" width="600">
</p>

### TrkPlotter.exe
TrkPlotter.exeは、PoseTracker.exeで得られた[キーポイント](#OpenPoseのキーポイント)間の距離等を計算し、グラフ描画するためのアプリケーションです。

グラフ描画対象のトラックファイルとイベントID、分析したい項目に応じた[計算項目ファイル](#計算項目ファイルcalclist)を設定し、「グラフ出力」ボタンをクリックすると描画が開始されます。
<p align="center">
  <img src="https://user-images.githubusercontent.com/49755007/108825631-9e246a00-7606-11eb-9806-e492795cf3fe.png" width="500">
</p>

## 導入

### 動作環境
- Windows10(x64)
- cuda 11.5 (PoseTracker.exeでのみ使用)
- cudnn 7 (PoseTracker.exeでのみ使用)
- Python 3.9
  - OpenCV 4.5
  - Pandas 1.2.5
  - Matplotlib 3.4.3
  - Scipy 1.7.1
  - Scikit-learn 1.0

### インストール
[こちら(v.0.3.0.0)](https://github.com/nishimura5/VideoObservation/releases/download/v0.3.0.0-beta/BehavioralObservation_0300.zip)からダウンロードしてzipを解凍し、インストーラーを起動してください。
別途[CUDA 11.5](https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=10)をインストールしてください。

## ファイルフォーマット
BehavioralObservationが扱うファイルフォーマットは次のとおりです。各ファイルを直接テキストエディタで編集する場合は、フォーマットに注意してください。

### ファイルのフォルダ構成
BehavioralObservationは上記の動画ファイル、[イベントファイル](#イベントファイルmevent)、[トラックファイル](#トラックファイルtrk)が、次のフォルダ構成で格納されていることを前提としています。

```bash
任意のフォルダ
├─mov
│  ├─aaaa.mp4
│  ├─...
│  └─zzzz.mp4
├─mevent
│  ├─aaaa.mevent    //MeventEditor.exeによって出力される
│  ├─...
│  └─zzzz.mevent
├─trk
│  ├─aaaa.trk       //PoseTracker.exeによって出力される
│  ├─aaaa_body.trk
│  ├─...
│  └─zzzz_body.trk
└─graph
   ├─aaaa.png       // TrkPlotter.exeによって出力される
   └─aaaa.csv
```

### 動画ファイル(.mp4, .mov, .avi)
OpenCVがサポートする動画ファイルに対応しています。

### イベントファイル(.mevent)
BehavioralObservation独自のファイルフォーマットです。イベントファイルはMeventEditor.exeで作成編集します。イベントファイルは動画と対になっており、動画と同じファイル名が付けられます。
イベントファイルはCSV形式で、下記のフィールドを有します。1行目はコメント行で、動画のfpsが記録されています。

||time|frame|mevent_id|comment|
|:---|:---|:---|:---|:---|
|名称|時刻|フレーム番号|イベントID|コメント|
|形式|HH:MM:SS.fff|int|int|str|
|例|00:01:22.200|2467|0|tark start|
|例|00:02:38.100|4738|0|tark end|

上記例では、0:1:22.2～0:2:38.1の間の区間がイベントID=0として観察の対象であることを意味します。

イベントファイルはPoseTracker.exeにおいて、解析対象の時刻範囲を指定する際に使用されます。

### トラックファイル(.trk)
BehavioralObservation独自のファイルフォーマットです。トラックファイルはPoseTracker.exeで生成します。
トラックファイルは第1フィールドと第2フィールドがマルチインデックスのCSV形式で、下記のフィールドを有します。
トラックファイルは動画と対になっており、動画と同じファイル名が付けられますが、適宜suffixが加えられます。

||frame|name|code|x|y|
|:---|:---|:---|:---|:---|:---|
|名称|フレーム番号|追跡対象名(1)|ランドマーク点(2)|x座標|y座標|
|形式|int|str|str|int|int|
|例|2467|0|0|389|853|
|例|2467|0|1|395|875|
||...|...|...|...|...|
|例|2467|0|69|517|889|

上記例では、フレーム番号2467において追跡対象0の[キーポイント0～69](#OpenPoseのキーポイント)のx,y座標がそれぞれ記録されています。

#### OpenPoseのキーポイント
![Keypoints of OpenPose](/optracker/img/keypoints.png)

### 計算項目ファイル(.calclist)
TrkPlotter.exeで点間距離等を計算するための設定ファイルフォーマットです。計算項目ファイルは開発者あるいはユーザーによって手入力で作成します。
計算項目ファイルの1行目はコメント行で、アプリケーションの選択メニューに表示される項目を記述します。
ファイル名には「_body」または「_face」というsuffixを記述します。計算項目ファイルに関する仕様は今後変更になる可能性があります。より詳細については[こちらを参照してください](trkproc/README.md)。

### ログファイル(.log)
BehavioralObservationはログファイル(optracker.log)をC:\ProgramData\BehavioralObservationに出力します。不具合が発生したときはログファイルから原因調査を試みてください。

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;

using Microsoft.WindowsAPICodePack.Dialogs;
using System.IO;
using System.Diagnostics;
using System.Configuration;

namespace PoseTracker
{
    /// <summary>
    /// MainWindow.xaml の相互作用ロジック
    /// </summary>
    public partial class MainWindow
    {
        private TargetFiles targetFiles = new TargetFiles();

        public MainWindow()
        {
            InitializeComponent();
            this.DataContext = this.targetFiles;
        }

        private void SelectAndOpenMovieButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new CommonOpenFileDialog("動画ファイル選択");
            dialog.IsFolderPicker = false;
            dialog.Filters.Add(new CommonFileDialogFilter("動画ファイル", "*.mp4;*.mov;*.avi"));

            // ダイアログを表示
            if (dialog.ShowDialog() == CommonFileDialogResult.Ok)
            {
                LoadMovieAndMevent(dialog.FileName);
            }
        }

        private void LoadMovieAndMevent(string movieFilePath)
        {
            // meventファイルのパスを生成
            string orgFolderPathStr = Path.GetDirectoryName(Path.GetDirectoryName(movieFilePath));
            string meventFileName = Path.GetFileNameWithoutExtension(movieFilePath);
            string meventFilePath = Path.Combine(orgFolderPathStr, "mevent", meventFileName + ".mevent");

            targetFiles.Add(movieFilePath, meventFilePath, ParseCombo(EditRot.Text, 0), ParseCombo(EditPeople.Text, 1), ParseCombo(EditEventId.Text, 0));
            int lastIdx = lstEntry.Items.Count - 1;

            lstEntry.SelectedIndex = lastIdx;
        }

        private int ParseCombo(string tarString, int defaultValue)
        {
            int res = defaultValue;
            if (Int32.TryParse(tarString, out res) == false)
            {
                res = defaultValue;
            }
            return res;
        }

        private void ListViewItem_Click(object sender, RoutedEventArgs e)
        {
            TargetFile selectedRow = (TargetFile)this.lstEntry.SelectedItem;
        }

        private void Remove_Click(object sender, RoutedEventArgs e)
        {
            targetFiles.Remove(lstEntry.SelectedIndex);
        }

        private void EditRow(string key, string value) {
            if (lstEntry == null) return;
            if (lstEntry.SelectedItems == null) return;
            List<string> movPathList = new List<string>();

            foreach (var current in lstEntry.SelectedItems)
            {
                TargetFile selectedRow = (TargetFile)current;
                movPathList.Add(selectedRow.MovPath);
            }
            var dic = new Dictionary<string, string>();
            foreach (var path in movPathList)
            {
                if (key == "rot")
                    targetFiles.EditRot(path, ParseCombo(value, 0));
                else if (key == "people")
                    targetFiles.EditPeople(path, ParseCombo(value, 1));
                else if (key == "eventid")
                    targetFiles.EditEventId(path, ParseCombo(value, 0));
            }
        }


        private void ExecuteTrackingButton_Click(object sender, RoutedEventArgs e)
        {
            ExecProcess("track");
        }

        private void GenBodyResultButton_Click(object sender, RoutedEventArgs e) {
            ExecProcess("body_play");
        }
        private void GenFaceResultButton_Click(object sender, RoutedEventArgs e)
        {
            ExecProcess("face_play");
        }

        private void ExecProcess(string mode) {
            List<TargetFile> targetFileList = new List<TargetFile>();
            targetFileList = targetFiles.GetFiletList();
            foreach (TargetFile targetFile in targetFileList)
            {
                string trkFolderPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(targetFile.MovPath)), "trk");
                string trkMovFilePath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(targetFile.MovPath)), "trkmov", targetFile.MovName);

                // 第1引数がコマンド、第2引数がコマンドの引数
                ProcessStartInfo app = new ProcessStartInfo();
                app.FileName = App.pythonExePath;
                app.Arguments = @"""" + App.pythonScriptPath + @"\optracker\face_tracking.py"" --mode "+mode+" --mov " + targetFile.MovPath + " -m " + targetFile.MeventPath + " --trk " + trkFolderPath + " -r " + targetFile.Rot.ToString() + " -o " + trkMovFilePath + " -p " + targetFile.People.ToString() + " -e " + targetFile.EventId.ToString() + " -s 0.4";
                // コマンド実行
                Process process = Process.Start(app);
                process.WaitForExit();
                process.Close();
            }

        }

        private void Rot_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            string newVal = (e.AddedItems[0] as ComboBoxItem).Content as string;
            EditRow("rot", newVal);
        }
        private void People_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            string newVal = (e.AddedItems[0] as ComboBoxItem).Content as string;
            EditRow("people", newVal);
        }
        private void EventId_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            string newVal = (e.AddedItems[0] as ComboBoxItem).Content as string;
            EditRow("eventid", newVal);
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            ProcessStartInfo app = new ProcessStartInfo();
            try
            {
                TargetFile selectedRow = (TargetFile)lstEntry.SelectedItem;
                if (selectedRow == null)
                {
                    throw new Exception("動画が選択されていません。");
                }
                string exePath = ConfigurationManager.AppSettings.Get("meventEditorPath");
                if (File.Exists(exePath) == false)
                {
                    throw new Exception("アプリケーションのパスが不正です。");
                }
                app.FileName = exePath;
                app.Arguments = selectedRow.MovPath;
                Process process = Process.Start(app);

            }
            catch (Exception ex)
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました\n" + ex.Message.ToString(), App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }

        }

        private void About_Click(object sender, RoutedEventArgs e)
        {
            About awin2 = new About();
            awin2.Show();
        }
    }
}

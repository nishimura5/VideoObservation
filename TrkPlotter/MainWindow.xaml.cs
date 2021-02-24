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
using Python.Runtime;
using System.IO;
using System.Diagnostics;
using System.Configuration;
using System.Threading;

namespace TrkPlotter
{
    /// <summary>
    /// MainWindow.xaml の相互作用ロジック
    /// </summary>
    public partial class MainWindow
    {
        public static dynamic genFile;
        private static double fps;
        public Dictionary<string, string> CalclistDict { get; set; }

        public MainWindow()
        {
            InitializeComponent();
            averageFrame.Text = ConfigurationManager.AppSettings.Get("defaultAverageFrame");
            xInterval.Text = Properties.Settings.Default.XInterval;
            graphWidth.Text = Properties.Settings.Default.GraphWidth;
            graphHeight.Text = Properties.Settings.Default.GraphHeight;
            yMin.Text = Properties.Settings.Default.YMin;
            yMax.Text = Properties.Settings.Default.YMax;

            CalclistDict = new Dictionary<string, string>();
            DataContext = this;

        }
        private void SelectAndOpenTrkButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new CommonOpenFileDialog("トラックファイル選択");
            dialog.IsFolderPicker = false;
            dialog.Filters.Add(new CommonFileDialogFilter("トラックファイル", "*.trk"));

            // ダイアログを表示
            if (dialog.ShowDialog() == CommonFileDialogResult.Ok)
            {
                trkFilePath.Text = dialog.FileName;
            }

            if (File.Exists(trkFilePath.Text) == true)
            {
                LoadTrkAndMevent();
            }
            pngSaveBtn.IsEnabled = false;
            csvSaveBtn.IsEnabled = false;
            openDestFolder.IsEnabled = false;
        }

        private void LoadTrkAndMevent()
        {
            // トラックファイルが置かれてるフォルダのパスを取得
            string orgFolderPathStr = Path.GetDirectoryName(trkFilePath.Text);
            string trkFolderNameStr = Path.GetFileName(orgFolderPathStr);
            // トラックファイルが置かれてるフォルダ名がtrkじゃなかったらエラー
            if (trkFolderNameStr != "trk")
            {
                return;
            }
            else
            {
                orgFolderPathStr = Path.GetDirectoryName(orgFolderPathStr);
            }

            // イベントファイルのパス生成
            string meventFileName = Path.GetFileNameWithoutExtension(trkFilePath.Text);
            string meventFilePathStr = Path.Combine(orgFolderPathStr, "mevent", meventFileName + ".mevent");

            if (File.Exists(meventFilePathStr) == false)
            {
                char[] separator = new char[] { '_' };
                string[] splittedStr = meventFileName.Split(separator, StringSplitOptions.RemoveEmptyEntries);
                string removedSuffix = splittedStr[0];
                for (int i = 1; i < splittedStr.Length - 1; i++)
                {
                    removedSuffix += "_" + splittedStr[i];
                }
                // トラックファイルにはsuffixが付くことがあるので除去
                meventFilePathStr = Path.Combine(orgFolderPathStr, "mevent", removedSuffix + ".mevent");
            }
            // suffix取ってもファイルがなければエラー
            if (File.Exists(meventFilePathStr) == false)
            {
                return;
            }
            meventFilePath.Text = meventFilePathStr;
            eventID.Items.Clear();
            using (Py.GIL())
            {
                dynamic meventEditor = App.meventModule.MeventEditor();
                fps = meventEditor.load(meventFilePath.Text);
                dynamic eventIdList = meventEditor.get_id_list();
                foreach (var id in eventIdList)
                {
                    eventID.Items.Add(id.ToString());
                }

                dynamic calclistList = App.plotModule.CalclistList(App.trkprocPath, trkFilePath.Text);
                dynamic calclistDict = calclistList.gen_calclist_dict();
                CalclistDict.Clear();
                foreach(dynamic pair in calclistDict.items())
                {
                    CalclistDict.Add(pair[0].ToString(), pair[1].ToString());
                }
            }
            meventEditBtn.IsEnabled = true;
            loadBtn.IsEnabled = true;
        }

        private void ShowProgressRing(bool active)
        {
            if (active == true)
            {
                fileSelectRow.Visibility = Visibility.Collapsed;
                loadTrkRow.Visibility = Visibility.Collapsed;
                setParamRow.Visibility = Visibility.Collapsed;
                progressRing.Visibility = Visibility.Visible;
            }
            else
            {
                fileSelectRow.Visibility = Visibility.Visible;
                loadTrkRow.Visibility = Visibility.Visible;
                setParamRow.Visibility = Visibility.Visible;
                progressRing.Visibility = Visibility.Hidden;
            }
        }

        private void LoadTrkButton_Click(object sender, RoutedEventArgs e)
        {
            ShowProgressRing(true);
            int averageFrameInt = TextBoxToInt(averageFrame);
            string tarTrkFilePath = trkFilePath.Text;
            string tarMeventFilePath = meventFilePath.Text;

            Task.Run(() =>
            {
                try
                {
                    genFile = App.plotModule.GenFile(tarTrkFilePath, tarMeventFilePath, averageFrameInt);
                }
                catch (Exception ex)
                {
                    MessageBoxResult result = MessageBox.Show("エラーが発生しました\n" + ex.Message.ToString(), App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
                }
                return true;
            }).ContinueWith((Task<bool> task) =>
            {
                Dispatcher.Invoke(() =>
                {
                    ShowProgressRing(false);
                    ConfigSave("defaultAverageFrame", averageFrameInt.ToString());
                });
            });
            pngSaveBtn.IsEnabled = true;
            csvSaveBtn.IsEnabled = true;
            openDestFolder.IsEnabled = true;
        }

        private SynchronizationContext _mainContext;


        private void SaveGraphButton_Click(object sender, RoutedEventArgs e)
        {
            if (genFile == null)
            {
                MessageBoxResult result = MessageBox.Show("トラックファイル読込を実行してください。", App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }
            ShowProgressRing(true);

            _mainContext = SynchronizationContext.Current;
            var task = StartSavePng();

        }

        private async Task StartSavePng()
        {
            string tarCalclistFilePath = Path.Combine(App.trkprocPath, calclistCombo.SelectedValue.ToString());
            string tarMeventFilePath = meventFilePath.Text;
            int tarGraphWidth = TextBoxToInt(graphWidth);
            int tarGraphHeight = TextBoxToInt(graphHeight);
            int tarXInterval = TextBoxToInt(xInterval);
            int tarYMin = TextBoxToInt(yMin);
            int tarYMax = TextBoxToInt(yMax);
            int tarEventId = int.Parse(eventID.Text);

            var ret = await Task.Run(() => SavePng(tarCalclistFilePath, tarMeventFilePath, tarGraphWidth, tarGraphHeight, tarXInterval, tarYMin, tarYMax, tarEventId));

            ShowProgressRing(false);
            if (ret == "ng")
            {
                MessageBoxResult result = MessageBox.Show("グラフ出力失敗", App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            Properties.Settings.Default.XInterval = xInterval.Text;
            Properties.Settings.Default.GraphWidth = graphWidth.Text;
            Properties.Settings.Default.GraphHeight = graphHeight.Text;
            Properties.Settings.Default.YMin = yMin.Text;
            Properties.Settings.Default.YMax = yMax.Text;
            Properties.Settings.Default.Save();
        }

        private string SavePng(string tarCalclistFilePath, string tarMeventFilePath, int tarGraphWidth, int tarGraphHeight, int tarXInterval, int tarYMin, int tarYMax, int tarEventId)
        {
            dynamic mevent = App.meventModule.ParseComment();
            mevent.load(tarMeventFilePath);
            mevent.select_event_id(tarEventId);
            // dynamic rectInfo = mevent.gen_rect_info(2, 4);
            //genFile.set_rect_info(rectInfo);

            genFile.set_tar_event_id(tarEventId);
            genFile.set_param(tarGraphWidth, tarGraphHeight, tarXInterval, tarYMin, tarYMax);
            genFile.set_fps(fps);
            var ok = genFile.load_calclist(tarCalclistFilePath);
            if (ok.ToString() != "ok")
            {
                return "ng";
            }
            ok = genFile.save_png();
            if (ok.ToString() != "ok")
            {
                return "ng";
            }
            return "ok";
        }

        private void SaveCsvButton_Click(object sender, RoutedEventArgs e)
        {
            string tarMeventFilePath = meventFilePath.Text;
            string tarCalclistFilePath = Path.Combine(App.trkprocPath, calclistCombo.SelectedValue.ToString());
            int tarEventId = int.Parse(eventID.Text);
            using (Py.GIL())
            {
                dynamic mevent = App.meventModule.ParseComment();
                mevent.load(tarMeventFilePath);
                mevent.select_event_id(tarEventId);
                genFile.set_tar_event_id(tarEventId);
                genFile.set_fps(fps);
                genFile.load_calclist(tarCalclistFilePath);
                genFile.save_csv();
            }
        }

        private int TextBoxToInt(TextBox tarTextBox)
        {
            int dstInt = 0;
            bool ok = int.TryParse(tarTextBox.Text, out dstInt);
            if (ok == false)
            {
                tarTextBox.Text = "0";
            }
            return dstInt;
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            string exePath = ConfigurationManager.AppSettings.Get("meventEditorPath");
            ProcessStartInfo app = new ProcessStartInfo();
            app.FileName = exePath;
            app.Arguments = @"""" + meventFilePath.Text + @"""";
            Process process = Process.Start(app);
        }

        private void ConfigSave(string key, string value)
        {
            Configuration configuration = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
            configuration.AppSettings.Settings[key].Value = value;
            configuration.Save();

            ConfigurationManager.RefreshSection("appSettings");
        }

        private void OpenDestFolder_Click(object sender, RoutedEventArgs e)
        {
            if (genFile == null)
            {
                return;
            }
            using (Py.GIL())
            {
                dynamic graphFolderPath = genFile.get_graph_path();
                System.Diagnostics.Process.Start("explorer.exe", graphFolderPath.ToString());
            }
        }

        private void About_Click(object sender, RoutedEventArgs e)
        {
            About awin2 = new About();
            awin2.Show();
        }
    }
}

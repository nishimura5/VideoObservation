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
using System.ComponentModel;
using System.Collections.ObjectModel;

namespace PoseTracker
{
    /// <summary>
    /// MainWindow.xaml の相互作用ロジック
    /// </summary>
    public partial class MainWindow
    {
        #region Binding
        internal class Bind : INotifyPropertyChanged
        {
            #region INotifyPropertyChanged
            public event PropertyChangedEventHandler PropertyChanged;
            protected virtual void OnPropertyChanged(string propertyName)
            {
                PropertyChangedEventHandler handler = this.PropertyChanged;
                if (handler != null)
                    handler(this, new PropertyChangedEventArgs(propertyName));
            }
            #endregion

            internal Bind() { }

            private ObservableCollection<TarFile> _TarFileProps;
            public ObservableCollection<TarFile> TarFileProps
            {
                get { return _TarFileProps; }
                set { _TarFileProps = value; OnPropertyChanged("TarFileProps"); }
            }
        }
        internal Bind _Bind;
        #endregion

        public List<int> rotList { get; set; }
        public List<int> peopleList { get; set; }
        public List<int> eventIdList { get; set; }
        public List<double> outScaleList { get; set; }

        public MainWindow()
        {
            InitializeComponent();

            rotList = new List<int>() {0, 90, 270};
            rotCombobox.ItemsSource = rotList;
            peopleList = new List<int>() {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
            peopleNumCombobox.ItemsSource = peopleList;
            eventIdList = new List<int>() {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
            eventIdCombobox.ItemsSource = eventIdList;
            outScaleList = new List<double>() { 1.0, 0.5, 0.25};
            outScaleCombobox.ItemsSource = outScaleList;

            _Bind = new Bind();
            this.DataContext = _Bind;
            _Bind.TarFileProps = new ObservableCollection<TarFile>();
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

            TarFile tarFile = new TarFile(movieFilePath, meventFilePath, 0, 1, 0, 1.0);
            _Bind.TarFileProps.Add(tarFile);
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

        private void Remove_Click(object sender, MouseButtonEventArgs e)
        {
            DependencyObject dep = (DependencyObject)e.OriginalSource;
            while ((dep != null) && !(dep is DataGridCell))
            {
                dep = VisualTreeHelper.GetParent(dep);
            }
            if (dep == null) return;

            if (dep is DataGridCell)
            {
                DataGridCell cell = dep as DataGridCell;
                cell.Focus();
                while ((dep != null) && !(dep is DataGridRow))
                {
                    dep = VisualTreeHelper.GetParent(dep);
                }
                DataGridRow row = dep as DataGridRow;
                tarFileDataGrid.SelectedItem = row.DataContext;
            }

            int idx = tarFileDataGrid.SelectedIndex;
            if (idx >= _Bind.TarFileProps.Count)
            {
                return;
            }
            _Bind.TarFileProps.RemoveAt(idx);
        }

        private void ListViewItem_Click(object sender, MouseButtonEventArgs e)
        {
            TarFile selectedRow = (TarFile)this.tarFileDataGrid.SelectedItem;
            if (selectedRow == null)
            {
                return;
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
            try {
                foreach (TarFile targetFile in _Bind.TarFileProps)
                {
                    string trkFolderPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(targetFile.MovPath)), "trk");
                    string trkMovFilePath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(targetFile.MovPath)), "trkmov", targetFile.MovName);

                    // 第1引数がコマンド、第2引数がコマンドの引数
                    ProcessStartInfo app = new ProcessStartInfo();
                    app.FileName = App.pythonExePath;
                    app.Arguments = @"""" + App.pythonScriptPath + @"\optracker\face_tracking.py"" --mode " + mode + 
                        @" --mov """ + targetFile.MovPath + 
                        @""" -m """ + targetFile.MeventPath + 
                        @""" --trk """ + trkFolderPath + 
                        @""" -r " + targetFile.Rot.ToString() + 
                        @" -o """ + trkMovFilePath + 
                        @""" -p " + targetFile.PeopleNum.ToString() + 
                        " -e " + targetFile.EventId.ToString() + 
                        " -s " + targetFile.OutScale.ToString();
                    // コマンド実行
                    Process process = Process.Start(app);
                    process.WaitForExit();
                    process.Close();
                }
            }
            catch (Exception ex)
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました\n" + ex.Message.ToString(), App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            ProcessStartInfo app = new ProcessStartInfo();
            try
            {
                TarFile selectedRow = (TarFile)this.tarFileDataGrid.SelectedItem;
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
                app.Arguments = @"""" + selectedRow.MovPath + @"""";
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

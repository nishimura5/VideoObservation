using System;
using System.Collections.Generic;
using System.Configuration;
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
using Microsoft.WindowsAPICodePack.Shell;
using Python.Runtime;
using System.Collections.ObjectModel;
using System.IO;
using System.Runtime.ExceptionServices;
using System.ComponentModel;


namespace MeventEditor
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

            private ObservableCollection<MeventData> _MeventDatas;
            public ObservableCollection<MeventData> MeventDatas
            {
                get { return _MeventDatas; }
                set { _MeventDatas = value; OnPropertyChanged("MeventDatas"); }
            }
        }
        internal Bind _Bind;
        #endregion

        private TargetMovie targetMovie = new TargetMovie();
        public List<int> eventIdList { get; set; }

        public MainWindow()
        {
            InitializeComponent();

            eventIdList = new List<int>(){0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
            eventIdCombobox.ItemsSource = eventIdList;

            _Bind = new Bind();
            this.DataContext = _Bind;
            _Bind.MeventDatas = new ObservableCollection<MeventData>();

            // コマンドライン引数からファイルパス取得した場合は画面開く際に動画とmeventも開く
            string moviePath = App.GetMovFilePathArg();

            movieFilePath.Text = moviePath;
            if (File.Exists(movieFilePath.Text) == true)
            {
                movieFilePath.Text = LoadMovieAndMevent(movieFilePath.Text);
            }
            else if (movieFilePath.Text != "")
            {
                MessageBoxResult result = MessageBox.Show("動画が見つかりませんでした", App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
                movieFilePath.Text = "";
            }
        }

        private void SelectAndOpenMovieButton_Click(object sender, RoutedEventArgs e)
        {
            Update();
            _Bind.MeventDatas.Clear();

            var dialog = new CommonOpenFileDialog("動画ファイル選択");
            dialog.IsFolderPicker = false;
            dialog.Filters.Add(new CommonFileDialogFilter("動画ファイル", "*.mp4;*.mov;*.avi"));

            // ダイアログを表示
            if (dialog.ShowDialog() == CommonFileDialogResult.Ok)
            {
                if (File.Exists(dialog.FileName) == true)
                {
                    dynamic ok;
                    using (Py.GIL())
                    {
                        ok = App.meventModule.is_all_ascii_in_path(dialog.FileName);
                    }
                    if(ok.ToString() == "ng")
                    {
                        MessageBoxResult result = MessageBox.Show("フォルダまたはファイル名に全角が含まれています。\nPoseTracker.exeを使用する場合はファイル名とフォルダ名を\n半角にしてください。", "注意", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                    movieFilePath.Text = LoadMovieAndMevent(dialog.FileName);
                }
            }
        }

        // 参照(動画ファイル)のクリックイベント
        private string LoadMovieAndMevent(string moviePath)
        {
            targetMovie.Pause();

            try
            {
                string newMoviePath;
                string newMeventPath;
                string fps = "30";
                using (Py.GIL())
                {
                    dynamic movPath = App.meventModule.move_file(moviePath, new string[] { "mov", "trkmov" });
                    newMoviePath = movPath.ToString();
                    dynamic meventPath = App.meventModule.gen_mevent_path(newMoviePath);
                    newMeventPath = meventPath.ToString();
                }

                movieWindowMediaElement.Source = new System.Uri(newMoviePath, UriKind.Relative);
                targetMovie.SetMediaElement(movieWindowMediaElement, progressSlider, playPauseButton, progressButton);

                targetMovie.Play();
                targetMovie.Pause();
                meventFilePath.Text = newMeventPath;

                // 動画のFPS取得
                ShellFile shellFile = ShellFile.FromFilePath(newMoviePath);
                float fFps = (float)shellFile.Properties.System.Video.FrameRate.Value / 1000;
                fps = fFps.ToString();
                if (fps.Length > 5)
                {
                    fps = fps.Substring(0, 5);
                }
                FpsLabel.Content = fps;

                double totalMs = targetMovie.GetTotalMs();

                using (Py.GIL())
                {
                    dynamic fpsInMevent = App.meventEditor.load(newMeventPath, fFps, (int)totalMs);
                    if ((float)fpsInMevent == 0)
                    {
                        App.meventEditor.set_fps(float.Parse(FpsLabel.Content.ToString()));
                    }

                    dynamic newEventList = App.meventEditor.get_event_list();
                    foreach (dynamic event_row in newEventList)
                    {
                        _Bind.MeventDatas.Add(new MeventData(event_row));
                    }
                }

                return newMoviePath;
            }
            catch (Exception ex)
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました\n" + ex.Message.ToString(), App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
                return "";
            }
        }

        private void PlayPauseButton_Click(object sender, RoutedEventArgs e)
        {
            if (targetMovie.GetState() == MediaState.Play)
            {
                targetMovie.Pause();
            }
            else if (targetMovie.GetState() == MediaState.Pause)
            {
                targetMovie.Play();
            }
        }

        private void MovieOpened(object sender, RoutedEventArgs e)
        {
            targetMovie.TimerStart();
            // ↓ファイルからアプリを開いたときにpauseアイコンをボタンに表示させるため
            targetMovie.Pause();
        }

        public void Update()
        {
            try
            {
                string meventPath = meventFilePath.Text;
                if (meventPath == "")
                {
                    return;
                }
                using (Py.GIL())
                {
                    {
                        App.meventEditor.update_mevent_file(_Bind.MeventDatas, meventPath);
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました(Update)\n" + ex.Message.ToString(), App.ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }
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
                meventDataGrid.SelectedItem = row.DataContext;
            }

            int idx = meventDataGrid.SelectedIndex;
            if (idx >= _Bind.MeventDatas.Count)
            {
                return;
            }
            _Bind.MeventDatas.RemoveAt(idx);
        }

        private void ProgressButton_Click(object sender, RoutedEventArgs e)
        {
            MeventData mevent = new MeventData(progressButton.Content.ToString().Substring(1), "0", "1", "--");
            _Bind.MeventDatas.Add(mevent);
            _Bind.MeventDatas = new ObservableCollection<MeventData>(_Bind.MeventDatas.OrderBy(n => n.Time));
        }

        private void Movie_MouseUp(object sender, RoutedEventArgs e)
        {
            int clickStepSecond = int.Parse(ConfigurationManager.AppSettings.Get("clickStepSecond"));
            targetMovie.Step(-1000 * clickStepSecond);
        }

        private void Button_MouseEnter(object sender, RoutedEventArgs e)
        {
            targetMovie.ChangeSpeed(0.5f);
        }
        private void Button_MouseLeave(object sender, RoutedEventArgs e)
        {
            targetMovie.ChangeSpeed(1.0f);
        }

        private void ListViewItem_Click(object sender, MouseButtonEventArgs e)
        {
            MeventData selectedRow = (MeventData)this.meventDataGrid.SelectedItem;
            if (selectedRow == null)
            {
                return;
            }
            targetMovie.Jump(selectedRow.Time);
        }

        private void Movie_MouseRightUp(object sender, MouseButtonEventArgs e)
        {
            int clickStepSecond = int.Parse(ConfigurationManager.AppSettings.Get("clickStepSecond"));
            targetMovie.Step(1000 * clickStepSecond);
        }

        // 一瞬sliderが0に戻ってしまうのを無理矢理修正
        private void Progress_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            double newValue = e.NewValue;
            if (newValue == 0)
            {
                progressSlider.Value = targetMovie.GetSliderValue();
            }
        }

        private void About_Click(object sender, RoutedEventArgs e)
        {
            About awin2 = new About();
            awin2.Show();
        }
        private void ClickStepSecond_Click(object sender, RoutedEventArgs e)
        {
            var item = ((MenuItem)sender);
            int clickStepSecond = int.Parse(ConfigurationManager.AppSettings.Get("clickStepSecond"));
            if (item.IsChecked)
            {
                clickStepSecond = 15;
            }
            else 
            {
                clickStepSecond = 5;
            }
            ConfigurationManager.AppSettings.Set("clickStepSecond", clickStepSecond.ToString());
        }
        private void Movie_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
        {
            if (e.Delta > 0)
            {
                targetMovie.ChangeSpeed(3.0f);
            }
            else if (e.Delta < 0)
            {
                targetMovie.ChangeSpeed(1.0f);

            }
        }
        [HandleProcessCorruptedStateExceptions]
        private void Window_Closing(object sender, CancelEventArgs e)
        {
            Update();
        }
    }
}

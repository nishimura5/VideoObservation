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

using Microsoft.WindowsAPICodePack.Shell;
using System.IO;

namespace TrkPlotter
{
    /// <summary>
    /// About.xaml の相互作用ロジック
    /// </summary>
    public partial class About : Window
    {
        public About()
        {
            string appName = "TrkPlotter.exe";
            InitializeComponent();
            Title = appName + "について";
            string exePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, appName);
            using (var file = ShellFile.FromFilePath(exePath))
            {
                file.Thumbnail.FormatOption = ShellThumbnailFormatOption.IconOnly;
                IconImage.Source = file.Thumbnail.BitmapSource; // 256x256
            }

            // バージョン
            var fullname = typeof(App).Assembly.Location;
            var info = System.Diagnostics.FileVersionInfo.GetVersionInfo(fullname);
            var ver = info.FileVersion;
            Version.Text = appName + "(Version:" + ver + ")";
        }
    }
}

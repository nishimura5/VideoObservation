using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
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

namespace MinicondaInstaller
{
    /// <summary>
    /// MainWindow.xaml の相互作用ロジック
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private void Install_ButtonClick(object sender, RoutedEventArgs e)
        {
            string installBatPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "miniconda_install.bat");

            // 第1引数がコマンド、第2引数がコマンドの引数
            ProcessStartInfo app = new ProcessStartInfo();
            app.FileName = installBatPath;
            app.Verb = "RunAs";
            // コマンド実行
            Process process = Process.Start(app);
            process.WaitForExit();
            process.Close();
            this.Close();
        }
    }
}

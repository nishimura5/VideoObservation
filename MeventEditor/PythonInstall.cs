﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using System.Diagnostics;
using System.IO;
using System.Windows;

namespace MeventEditor
{
    class PythonInstall
    {
        static public void ExecuteInstall() {
            string installBatPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "miniconda_install.bat");

            // 第1引数がコマンド、第2引数がコマンドの引数
            ProcessStartInfo app = new ProcessStartInfo();
            app.FileName = installBatPath;
            app.Verb = "RunAs";
            // コマンド実行
            Process process = Process.Start(app);
            process.WaitForExit();
            process.Close();
        }
    }
}

﻿using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;

using Python.Runtime;
using System.IO;
using ControlzEx.Theming;
using System.Runtime.ExceptionServices;
using System.Diagnostics;

namespace TrkPlotter
{
    /// <summary>
    /// App.xaml の相互作用ロジック
    /// </summary>
    public partial class App : Application
    {
        public static dynamic plotModule;
        public static dynamic meventModule;
        private static string trkFilePathArg = "";
        public static string ERROR_DIALOG_TITLE = "MeventEditor Error!";
        public static string trkprocPath;

        public static void AddEnvPath(params string[] paths)
        {
            try
            {
                var envPaths = Environment.GetEnvironmentVariable("PATH").Split(Path.PathSeparator).ToList();
                foreach (var path in paths)
                {
                    if (path.Length > 0 && !envPaths.Contains(path))
                    {
                        envPaths.Insert(0, path);
                    }
                }
                Environment.SetEnvironmentVariable("PATH", string.Join(Path.PathSeparator.ToString(), envPaths), EnvironmentVariableTarget.Process);
            }
            catch
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました(AddEnvPath)", ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void OnStartUp(object sender, StartupEventArgs e)
        {
            // 引数チェック
            foreach (string arg in e.Args)
            {
                trkFilePathArg = arg;
            }
            // meventからアプリを開いた場合は動画ファイルを探索する
            if (Path.GetExtension(trkFilePathArg) == ".mevent")
            {
                string parentPath = Path.GetDirectoryName(Path.GetDirectoryName(trkFilePathArg));
                string baseName = Path.GetFileNameWithoutExtension(trkFilePathArg);
                string trkPath = Path.Combine(parentPath, "trk", baseName + ".trk");

                trkFilePathArg = trkPath;
            }

            // 実行ファイルのパス、規定値で目当てのモジュールが見つからなかったらApp.configの値を参照
            string EXEDIR = AppDomain.CurrentDomain.BaseDirectory;
            if (File.Exists(Path.Combine(EXEDIR, "mevent")) == false)
            {
                EXEDIR = ConfigurationManager.AppSettings.Get("pyScriptPath");
            }
            trkprocPath = Path.Combine(EXEDIR, "trkproc");

            // *-------------------------------------------------------*
            // * python環境の設定
            // *-------------------------------------------------------*

            // python環境にパスを通す、規定値でpython.exeが見つからなかったらApp.configの値を参照
            var PYTHON_HOME = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "miniconda38_64");
            if (File.Exists(Path.Combine(PYTHON_HOME, "python.exe")) == false)
            {
                PYTHON_HOME = ConfigurationManager.AppSettings.Get("pythonPath");
            }
            // ついにpython環境が見つからなかったらMinicondaインストール
            if (File.Exists(Path.Combine(PYTHON_HOME, "python.exe")) == false)
            {
                string installBatPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "MinicondaInstaller.exe");
                // 第1引数がコマンド、第2引数がコマンドの引数
                ProcessStartInfo app = new ProcessStartInfo();
                app.FileName = installBatPath;
                // コマンド実行
                Process process = Process.Start(app);
                process.WaitForExit();
                process.Close();
                PYTHON_HOME = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "miniconda38_64");
            }

            // pythonnetが、python本体のDLLおよび依存DLLを見つけられるようにする
            AddEnvPath(
                  PYTHON_HOME,
                  Path.Combine(PYTHON_HOME, @"Library\bin")
                );

            // python環境に、PYTHON_HOME(標準pythonライブラリの場所)を設定
            PythonEngine.PythonHome = PYTHON_HOME;

            // python環境に、PYTHON_PATH(モジュールファイルのデフォルトの検索パス)を設定
            PythonEngine.PythonPath = string.Join(
              Path.PathSeparator.ToString(),
              new string[] {
                  PythonEngine.PythonPath,// 元の設定を残す
                  Path.Combine(PYTHON_HOME, @"Lib\site-packages"), //pipで入れたパッケージはここに入る
                  Path.Combine(EXEDIR), //自分で作った(動かしたい)pythonプログラムの置き場所も追加
              }
            );

            try
            {
                // 初期化 (明示的に呼ばなくても内部で自動実行されるようだが、一応呼ぶ)
                PythonEngine.Initialize();

                // *-------------------------------------------------------*
                // * pythonコードの実行
                // *-------------------------------------------------------*
                // Global Interpreter Lockを取得
                // importを2回実行すると例外を吐く対策
                using (Py.GIL())
                {
                    meventModule = Py.Import("mevent");
                    plotModule = Py.Import("trkproc");
                }
            }
            catch (Exception ex)
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました(OnStartUp)\n" + ex.Message.ToString(), ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        public static string getMovFilePathArg()
        {
            return trkFilePathArg;
        }

        [HandleProcessCorruptedStateExceptions]
        private void OnExit(object sender, ExitEventArgs e)
        {
            try
            {
                // python環境を破棄
                PythonEngine.Shutdown();
            }
            catch (AccessViolationException ex)
            {
                MessageBoxResult result = MessageBox.Show("エラーが発生しました(OnExit)\n" + ex.Message.ToString(), ERROR_DIALOG_TITLE, MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}

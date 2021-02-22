using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using System.Windows.Threading;


namespace MeventEditor
{
    class TargetMovie
    {
        private MediaState m_stateCurrent;
        private MediaElement movie;
        private Slider ProgressSlider;
        private Button playPause;
        private Button ProgressLabel;
        private double lastSliderValue;
        private DispatcherTimer m_timer;

        public void SetMediaElement(MediaElement mediaElement, Slider progressSlider, Button playPauseButton, Button progressButton)
        {
            movie = mediaElement;
            ProgressSlider = progressSlider;
            ProgressLabel = progressButton;
            playPause = playPauseButton;

            // タイマー設定
            m_timer = new DispatcherTimer();
            m_timer.Interval = TimeSpan.FromMilliseconds(10);
            m_timer.Tick += DispatcherTimer_Tick;
        }

        public void TimerStart()
        {
            if (m_timer != null)
            {
                m_timer.Start();
            }
        }

        public void TimerStop()
        {
            if (m_timer != null)
            {
                m_timer.Stop();
            }
        }

        private void DispatcherTimer_Tick(object sender, EventArgs e)
        {
            SyncSliderAndSeek();
            string position = movie.Position.ToString();
            if (position.Length > 10)
            {
                position = position.Substring(0, 10);
            }
            ProgressLabel.Content = position;
        }

        public MediaState GetState()
        {
            return m_stateCurrent;
        }

        public double GetSliderValue()
        {
            return lastSliderValue;
        }

        public void SyncSliderAndSeek()
        {
            if (m_stateCurrent == MediaState.Play || m_stateCurrent == MediaState.Pause)
            {
                if (lastSliderValue == ProgressSlider.Value)
                {
                    // 動画経過時間に合わせてスライダーを動かす
                    double dbPrg = GetMovieProgress();
                    ProgressSlider.Value = dbPrg * ProgressSlider.Maximum;
                    lastSliderValue = ProgressSlider.Value;
                    if (GetMediaState() == MediaState.Pause && m_stateCurrent == MediaState.Play)
                    {
                        movie.Play();
                    }
                }
                else
                {
                    // Sliderを操作したとき
                    if (m_stateCurrent == MediaState.Play)
                    {
                        movie.Pause();
                    }
                    // スライダーを動かした位置に合わせて動画の再生箇所を更新する
                    double dbSliderValue = ProgressSlider.Value;
                    double dbDurationMS = movie.NaturalDuration.TimeSpan.TotalMilliseconds;
                    int nSetMS = (int)(dbSliderValue * dbDurationMS / ProgressSlider.Maximum);
                    movie.Position = TimeSpan.FromMilliseconds(nSetMS);
                    lastSliderValue = ProgressSlider.Value;
                }
            }
        }

        public double GetTotalMs()
        {
            for (int i=0; i<100000; i++)
            {
                var _ = Wait();
                if (movie.NaturalDuration.HasTimeSpan == true)
                {
                    return movie.NaturalDuration.TimeSpan.TotalMilliseconds;
                }
            }
            return 0;
        }

        private async Task<string> Wait()
        {
            await Task.Delay(10);
            return "end";
        }

        public void Back(int msec)
        {
            double dbSliderValue = ProgressSlider.Value;
            if (movie.NaturalDuration.HasTimeSpan == false)
            {
                return;
            }
            double dbDurationMS = movie.NaturalDuration.TimeSpan.TotalMilliseconds;
            int nSetMS = (int)(dbSliderValue * dbDurationMS / ProgressSlider.Maximum);

            int newMs = nSetMS - msec;
            if (newMs < 0)
            {
                newMs = 0;
            }
            ProgressSlider.Value = (int)(newMs / dbDurationMS);
            lastSliderValue = ProgressSlider.Value;
            movie.Position = TimeSpan.FromMilliseconds(newMs);
        }

        public void Jump(string time)
        {
            DateTime jumpDt;
            CultureInfo jpjp = new CultureInfo("jp-Jp");
            time = "1900/01/01 " + time;
            bool res = DateTime.TryParseExact(time, "yyyy/MM/dd H:mm:ss", CultureInfo.InvariantCulture, DateTimeStyles.None, out jumpDt);
            if (res == false)
            {
                res = DateTime.TryParseExact(time, "yyyy/MM/dd H:mm:ss.f", CultureInfo.InvariantCulture, DateTimeStyles.None, out jumpDt);
            }

            DateTime origin = new DateTime(1900, 1, 1, 0, 0, 0, 0, DateTimeKind.Utc);
            TimeSpan diff = jumpDt - origin;
            double mseconds = diff.TotalMilliseconds;
            double dbDurationMS = movie.NaturalDuration.TimeSpan.TotalMilliseconds;
            ProgressSlider.Value = (int)(mseconds / dbDurationMS);
            movie.Position = TimeSpan.FromMilliseconds(mseconds);
            lastSliderValue = ProgressSlider.Value;
        }

        // ステータス取得
        private MediaState GetMediaState()
        {
            System.Reflection.FieldInfo hlp = typeof(MediaElement).GetField("_helper", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            object helperObject = hlp.GetValue(movie);
            System.Reflection.FieldInfo stateField = helperObject.GetType().GetField("_currentState", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            MediaState state = (MediaState)stateField.GetValue(helperObject);
            return state;
        }

        // 再生位置取得
        private double GetMovieProgress()
        {
            double dbPrg;
            try
            {
                TimeSpan tsCrnt = movie.Position;
                TimeSpan tsDuration = movie.NaturalDuration.TimeSpan;
                dbPrg = tsCrnt.TotalMilliseconds / tsDuration.TotalMilliseconds;
            }
            catch (InvalidOperationException)
            {
                dbPrg = 0;
            }
            return dbPrg;
        }
        public void Pause()
        {
            if (movie != null)
            {
                movie.Pause();
                m_stateCurrent = MediaState.Pause;
                SetButtonImage("play.png");
            }
        }
        public void Play()
        {
            if (movie != null)
            {
                movie.Play();
                m_stateCurrent = MediaState.Play;
                SetButtonImage("pause.png");
            }
        }

        private void SetButtonImage(string fileName)
        {
            var brush = new ImageBrush();
            brush.ImageSource = new BitmapImage(new Uri("pack://application:,,,/MeventEditor;component/Images/" + fileName));
            brush.Stretch = Stretch.Uniform;
            Rectangle rect = new Rectangle();
            rect.Width = playPause.ActualWidth;
            rect.Height = 15;
            rect.Fill = brush;
            playPause.Content = rect;
        }

        public void ChangeSpeed(double ratio)
        {
            if (m_stateCurrent == MediaState.Play)
            {
                movie.SpeedRatio = ratio;
            }
        }

    }
}

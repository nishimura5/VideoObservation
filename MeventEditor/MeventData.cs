using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

using System.Windows.Input;

namespace MeventEditor
{
    public class MeventData
    {
        public string Time { get; set; }
        public int Frame { get; set; }
        public int EventId { get; set; }
        public string Comment { get; set; }

        public MeventData()
        {
            Time = "00:00:00.0";
            Frame = 0;
            EventId = 0;
            Comment = "";
        }

        public MeventData(dynamic event_row)
        {
            Time = event_row[0];
            Frame = event_row[1];
            EventId = event_row[2];
            Comment = event_row[3];
        }

        public MeventData(string EntryTime, string EntryFrame, string EntryEventId, string EntryComment)
        {
            int frame;
            if (Int32.TryParse(EntryFrame, out frame) == false)
            {
                frame = 0;
            }
            int eventId;
            if (Int32.TryParse(EntryEventId, out eventId) == false)
            {
                eventId = 0;
            }
            Time = EntryTime;
            Frame = frame;
            EventId = eventId;
            Comment = EntryComment;
        }
    }
}

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using System.IO;

namespace PoseTracker
{
    class TargetFiles
    {
        public ObservableCollection<TargetFile> Items { get { return _Items; } }
        private ObservableCollection<TargetFile> _Items = new ObservableCollection<TargetFile>();

        public void Add(string Movpath, string MeventPath, int Rot, int People, int EventId)
        {
            _Items.Add(new TargetFile(Movpath, MeventPath, Rot, People, EventId));
        }

        public void Remove(int n)
        {
            if ((n >= 0) && (n < Items.Count))
            {
                _Items.RemoveAt(n);
            }
        }

        public void EditRot(string Movpath, int Rot)
        {
            for (int i = 0; i < _Items.Count; i++)
            {
                if (_Items[i].MovPath == Movpath)
                {
                    _Items[i] = new TargetFile(Movpath, _Items[i].MeventPath, Rot, _Items[i].People, _Items[i].EventId);
                }
            }
        }
        public void EditPeople(string Movpath, int People)
        {
            for (int i = 0; i < _Items.Count; i++)
            {
                if (_Items[i].MovPath == Movpath)
                {
                    _Items[i] = new TargetFile(Movpath, _Items[i].MeventPath, _Items[i].Rot, People, _Items[i].EventId);
                }
            }
        }
        public void EditEventId(string Movpath, int EventId)
        {
            for (int i = 0; i < _Items.Count; i++)
            {
                if (_Items[i].MovPath == Movpath)
                {
                    _Items[i] = new TargetFile(Movpath, _Items[i].MeventPath, _Items[i].Rot, _Items[i].People, EventId);
                }
            }
        }

        public List<TargetFile> GetFiletList()
        {
            List<TargetFile> data = new List<TargetFile>();
            int numberOfRow = _Items.Count;
            for (int i = 0; i < numberOfRow; i++)
            {
                var row = new TargetFile(_Items[i].MovPath, _Items[i].MeventPath, _Items[i].Rot, _Items[i].People, _Items[i].EventId);
                data.Add(row);
            }
            return data;
        }
    }

    public class TargetFile
    {
        public string MovPath { get; set; }
        public string MeventPath { get; set; }
        public string MovName { get; set; }
        public string MeventName { get; set; }
        public int Rot { get; set; }
        public int People { get; set; }
        public int EventId { get; set; }


        public TargetFile(string EntryMovPath, string EntryMeventPath, int EntryRot, int EntryPeople, int EntryEventId)
        {
            MovPath = EntryMovPath;
            MovName =  Path.GetFileName(MovPath);
            MeventPath = EntryMeventPath;
            MeventName = Path.GetFileName(MeventPath);
            Rot = EntryRot;
            People = EntryPeople;
            EventId = EntryEventId;
        }
    }
}

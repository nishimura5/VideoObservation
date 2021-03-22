using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace PoseTracker
{
    class TarFile
    {
        public string MovPath { get; set; }
        public string MovName { get; set; }
        public string MeventPath { get; set; }
        public string MeventName { get; set; }
        public int Rot { get; set; }
        public int PeopleNum { get; set; }
        public int EventId { get; set; }

        public TarFile()
        {
            MovPath = "";
            MovName = "";
            MeventPath = "";
            MeventName = "";
            Rot = 0;
            PeopleNum = 1;
            EventId = 0;
        }

        public TarFile(string DefMovPath, string DefMeventPath, int DefRot, int DefPeopleNum, int DefEventId)
        {
            MovPath = DefMovPath;
            MovName = Path.GetFileName(MovPath);
            MeventPath = DefMeventPath;
            MeventName = Path.GetFileName(MeventPath);
            Rot = DefRot;
            PeopleNum = DefPeopleNum;
            EventId = DefEventId;
        }
    }
}

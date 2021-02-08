#!/usr/bin/python3
#

"""Tests for results.py"""

import startlists


def test_parse_scb():
    """Ensure we can parse the scb format correctly"""
    lines = """#18 BOYS 10&U 50 FLY
                    --                
                    --                
                    --                
PERSON, JUST A      --TEAM            
                    --                
BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                    --                
                    --                
                    --                
                    --                
                    --                
                    --                
                    --                
XXXXXXX, YYYYYY Z   --                
                    --                
AAAAA, B            --X               
                    --                
                    --                
                    --                
                    --                """.split("\n")
    assert len(lines) == 21
    evt = startlists.Event()
    evt.from_lines(lines)
    print("--- Event Object Data Dump ---")
    evt.dump()

    # Indexes are 1 less than the heat number

    print("---> Heat 1 Assertions <----")
    assert evt.event_desc == "BOYS 10&U 50 FLY"
    assert evt.heats[0].lanes[3].name == "PERSON, JUST A"
    assert evt.heats[0].lanes[3].team == "TEAM"
    assert evt.heats[0].lanes[5].name == "BIGBIGBIGLY, NAMENAM"
    assert evt.heats[0].lanes[5].team == "LONGLONGLONGLONG"
    assert not evt.heats[0].lanes[3].is_empty()
    assert evt.heats[0].lanes[4].is_empty()

    print("---> Heat 2 Assertions <----")
    assert evt.heats[1].lanes[3].name == "XXXXXXX, YYYYYY Z"
    assert evt.heats[1].lanes[3].team == ""
    assert evt.heats[1].lanes[5].name == "AAAAA, B"
    assert evt.heats[1].lanes[5].team == "X"

    print("--- All Tests Passed ---")

if __name__ == "__main__":
    test_parse_scb()

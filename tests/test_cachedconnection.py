from httpkom import kom


def test_read_ranges_to_gaps_and_last_with_empty_list():
    c = kom.CachedConnection(None)
    read_ranges = []
    
    gaps, last = c.read_ranges_to_gaps_and_last(read_ranges)
    
    assert len(gaps) == 0
    assert last == 1

def test_read_ranges_to_gaps_and_last_with_one_empty_read_range():
    c = kom.CachedConnection()
    read_ranges = [ kom.ReadRange() ]
    
    gaps, last = c.read_ranges_to_gaps_and_last(read_ranges)
    
    assert len(gaps) == 0
    assert last == 1

def test_read_ranges_to_gaps_and_last():
    c = kom.CachedConnection()
    read_ranges = [ kom.ReadRange(1, 1),
                    kom.ReadRange(2, 3),
                    kom.ReadRange(5, 5),
                    kom.ReadRange(8, 10) ]
    
    gaps, last = c.read_ranges_to_gaps_and_last(read_ranges)
    
    assert last == 11
    assert len(gaps) == 2
    assert gaps == [(4, 1), (6, 2)]


class MockResponse(object):
    def __init__(self, resp):
        self.resp = resp
    
    def response(self):
        return self.resp

def create_local_to_global(highest_local):
    def local_to_global(conn, conf, first, n):
        if first > highest_local:
            print "first is greater than highest local (first: %d, highest_local: %d" % (
                first, highest_local)
            raise kom.NoSuchLocalText()
        
        mapping = kom.TextMapping()
        mapping.range_begin = first
        mapping.range_end = min(first + n, highest_local + 1)
        mapping.later_texts_exists = 0 if mapping.range_end > highest_local else 1
        mapping.type_text = "dense"
        mapping.list = [ (i, i) for i in range(mapping.range_begin, mapping.range_end) ]
        print mapping
        return MockResponse(mapping)
    return local_to_global

def test_get_unread_texts_from_membership_small():
    membership = kom.Membership()
    membership.conference = 1
    membership.read_ranges = [
        kom.ReadRange(1, 1), kom.ReadRange(2, 3), kom.ReadRange(5, 5), kom.ReadRange(8, 10) ]
    last_text = 12
    c = kom.CachedConnection(kom.RequestFactory({
                'local-to-global': create_local_to_global(last_text) }))
    
    unread_texts = c.get_unread_texts_from_membership(membership)
    
    assert unread_texts == [4, 6, 7, 11, 12]

def test_get_unread_texts_from_membership_large():
    membership = kom.Membership()
    membership.conference = 1
    membership.read_ranges = [
        kom.ReadRange(1, 300), kom.ReadRange(1000, 2000), kom.ReadRange(2100, 3000) ]
    highest_local = 4000
    c = kom.CachedConnection(kom.RequestFactory({
                'local-to-global': create_local_to_global(highest_local) }))
    
    unread_texts = c.get_unread_texts_from_membership(membership)
    
    assert unread_texts == range(301, 1000) + range(2001, 2100) + range(3001, highest_local+1)

def test_get_unread_texts_from_membership_fetches_the_correct_mappings():
    """This regression test checks that we can handle a gap that is
    larger than what can be fetched in one request (was limited to 255
    in the code, not by the server). Before the bug was fixed it
    wouldn't continue correctly.
    
    With last_text == 257 it would send these local-to-global request (first, num):
      1, 255
      1, 1
      258, 255 # this gets a "no-such-local-text" error, which aborts the loop
      
    where the correct behavior is:
      1, 255
      256, 1
      258, 255 # this gets a "no-such-local-text" error, which aborts the loop

    """
    first_problem = 256
    last_text = first_problem + 1
    membership = kom.Membership()
    membership.conference = 1
    membership.read_ranges = [ kom.ReadRange(last_text, last_text) ]
    c = kom.CachedConnection(kom.RequestFactory({
                'local-to-global': create_local_to_global(last_text) }))
    
    unread_texts = c.get_unread_texts_from_membership(membership)
    
    assert unread_texts is not None
    assert len(unread_texts) == len(set(unread_texts))
    assert len(unread_texts) == last_text - 1
    assert unread_texts == range(1, last_text)

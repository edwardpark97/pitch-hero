import midi
pattern_guide = midi.read_midifile("guide2.mid")
pattern_player = midi.read_midifile("player2.mid")
print pattern_guide
print pattern_player

guide_data = []
player_data = []

# guide_time = 0
# player_time = 0

guide_time = 8.
player_time = 16.

k = 1.0/192.0

# k = 1.0/160.0

for event in pattern_guide[0]:
	if type(event) == midi.events.NoteOnEvent:
		guide_time += event.tick * k
		guide_data.append([guide_time, event.data[0], 0])
	elif type(event) == midi.events.NoteOffEvent:
		guide_time += event.tick * k

for event in pattern_player[0]:
	if type(event) == midi.events.NoteOnEvent:
		player_time += event.tick * k
		player_data.append([player_time, event.data[0], 1])
	elif type(event) == midi.events.NoteOffEvent:
		player_time += event.tick * k


player_data_idx = 0
guide_data_idx = 0

time_mult = 6.0/5.0

for i in range(len(player_data) + len(guide_data)):
	if len(guide_data) <= guide_data_idx or player_data[player_data_idx][0] < guide_data[guide_data_idx][0]:
		print "%f\t%d\t%d" % (player_data[player_data_idx][0]*time_mult, player_data[player_data_idx][1] - 24, player_data[player_data_idx][2])
		player_data_idx += 1
	else:
		print "%f\t%d\t%d" % (guide_data[guide_data_idx][0]*time_mult, guide_data[guide_data_idx][1] - 24, guide_data[guide_data_idx][2])
		guide_data_idx += 1

#include <iostream>
#include <vector>
#include <set>

using namespace std;

void generate(vector<short>&, const short);

vector< vector<short> > boards;

// number of dimensions that will be generated:
// dim 0-8: tic-tac-toe 3x3 grid values
// dim 9-13: state heuristics
// 	dim 9-10: 	# possible lines that can form from existing marks, with respect to each player
// 	dim 11-12: 	# of those lines with 2 or more marks, with respect to each player
//	dim 13: 	if valid, which player won, else 0. possible values are -1, 0, and 1,
const short num_dim = 14; //9 + 5;

int main(int argc, char const *argv[])
{
	vector<short> board(num_dim, 0);
	generate(board, 1);
	static set< vector<short> > s(boards.begin(), boards.end());
	boards.assign(s.begin(), s.end());
	s.clear();
	//cout << boards.size() << ",  " << boards[0].size() << endl;
	for (unsigned long i = 0; i < boards.size(); ++i)
	{
		cout << boards[i][0];
		for (unsigned short j = 1; j < boards[i].size(); ++j)
			cout << ' ' << boards[i][j];

		cout << endl;
	}
	boards.clear();
	return 0;
}

// function that checks 3 grid spaces and calculates and returns heuristics 
// note:
//	function assumes (x1, y1), (x2, y2), and (x3, y3) are form 3 unit length line in the 3x3 board
//	function doesn't check if values are indeed a line
//	even if heuristic metrics aren't used, function is needed to calculate whether a player has won
// args:
//	b: 3x3 board state
//	m: vector of length 5, that heuristic calculations will be stored in
//	(xn, yn): position in board to check
void check_line(const vector< vector<short> >& b, vector<short>& m, const short x1, const short y1, const short x2, const short y2, const short x3, const short y3)
{
	/* Oct 20, 2018 - 
	//	I wrote this program over 5 months ago. I finally added comments today
	//	but I apologize to whoever is reading it
	//	because I won't be adding comments in this function.
	//	I realize it seems cryptic...
	//	...wait. Nvm, as I was writing this, I somehow understand what this function does again
	*/
	if (b[x1][y1] || b[x2][y2] || b[x3][y3])
	{
		if (b[x1][y1] && b[x2][y2] && b[x3][y3] && (b[x2][y2] == b[x1][y1]) && (b[x2][y2] == b[x3][y3]))
			if (b[x2][y2] > 0)
			{
				m[0] += 1;
				m[2] += 1;
				if (!m[4]) m[4] = 1;
			}
			else
			{
				m[1] += 1;
				m[3] += 1;
				if (!m[4]) m[4] = -1;
			}
		else if (b[x2][y2] && b[x1][y1] && (b[x2][y2] == b[x1][y1]) && (b[x3][y3] == 0))
			if (b[x2][y2] > 0)
			{
				m[0] += 1;
				m[2] += 1;
			}
			else
			{
				m[1] += 1;
				m[3] += 1;
			}
		else if (b[x2][y2] && b[x3][y3] && (b[x2][y2] == b[x3][y3]) && (b[x1][y1] == 0))
			if (b[x2][y2] > 0)
			{
				m[0] += 1;
				m[2] += 1;
			}
			else
			{
				m[1] += 1;
				m[3] += 1;
			}
		else if (b[x1][y1] && b[x3][y3] && (b[x1][y1] == b[x3][y3]) && (b[x2][y2] == 0))
			if (b[x1][y1] > 0)
			{
				m[0] += 1;
				m[2] += 1;
			}
			else
			{
				m[1] += 1;
				m[3] += 1;
			}
		else if ((b[x1][y1] == b[x2][y2] && !b[x2][y2]) || (b[x2][y2] == b[x3][y3] && !b[x3][y3]) || (b[x1][y1] == b[x3][y3] && !b[x1][y1]))
			if ((b[x1][y1] + b[x2][y2] + b[x3][y3]) == 1)
				m[0] += 1;
			else
				m[1] += 1;
	}
}

// generate all possible board states and push it into global variable "boards"
// args:
//	b: 3x3 board state
//	turn: value representing turn player. Either -1 or 1
void generate(vector<short>& b, const short turn)
{
	// heuristic metric: # possible lines that can form from existing marks, # of those lines with 2 or more marks, game winner
	vector<short> metrics(5, 0);
	vector< vector<short> > board(3, vector<short>(3, 0));
	for (unsigned short i = 0; i < 3; ++i)
	{
		const unsigned short ii = i*3;
		for (unsigned short j = 0; j < 3; ++j)
			if (b[ii + j])
				board[i][j] = b[ii + j];
	}

	for (unsigned short i = 0; i < 3; ++i)
	{
		check_line(board, metrics, i, 0, i, 1, i, 2);
		check_line(board, metrics, 0, i, 1, i, 2, i);
	}
	check_line(board, metrics, 0, 0, 1, 1, 2, 2);
	check_line(board, metrics, 0, 2, 1, 1, 2, 0);

	if (num_dim > 9) b[9] = metrics[0];
	if (num_dim > 10) b[10] = metrics[1];
	if (num_dim > 11) b[11] = metrics[2];
	if (num_dim > 12) b[12] = metrics[3];
	if (num_dim > 13) b[13] = metrics[4];
	
	boards.push_back(b);
	
	// end recursive branch if a player has won or game is tied 
	if (metrics[4] || (b[0] && b[1] && b[2] && b[3] && b[4] && b[5] && b[6] && b[7] && b[8])) return;
	// otherwise check the next possible move
	else
		for (unsigned short i = 0; i < 9; ++i)
			if (b[i] == 0)
			{
				b[i] = turn;
				generate(b, -turn);
				b[i] = 0;
			}
}

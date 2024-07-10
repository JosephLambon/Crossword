import sys
import copy
import random

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for node in copy.deepcopy(self.domains): # Loop over crossword nodes
            for word in self.domains[node]: # Loop over all words in each node's domain
                if len(word) != node.length:
                    self.domains[node].remove(word) # Remove words not equal to length of node

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.
        Return True if a revision was made to the of `x`; return
        False if no revision was made
        """
        if self.crossword.overlaps[x,y] == None: 
            raise AssertionError # If no overlap, raise Error
        
        i,j = self.crossword.overlaps[x,y] # return the co-ordinates of overlap
        revised = False
        for word_x in self.domains[x]: # Loop over words in x's domain
            arcConsistent = False
            for word_y in self.domains[y]: # Loop over words in y's domain
                if word_x[i] == word_y[j]: 
                    arcConsistent = True
            if not arcConsistent:
                self.domains[x].remove(word_x) # If not arc consistent, remove word from x domain
                revised = True # Confirm x domain was updated
            
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        """start with an initial queue of all of the arcs in the problem."""
        if not arcs:
            queue = [] # Initialise empty queue
            for node in copy.deepcopy(self.domains): # Loop over nodes
                neighbors = self.crossword.neighbors(node) # Get neighbors for node
                for neighbor in neighbors:
                    queue.append((node,neighbor)) # Add arc to queue for each node
    
        # Otherwise, begin with queue of only the arcs in the list arcs (where each arc is a tuple (x, y) of a variable x and a different variable y).
        queue = [(i,j) for (i,j) in arcs]
        
        while queue not empty:
            (i,j) = queue.pop(0) # Remove the first tuple from the queue, & assign to (i,j)
            if revise(i,j): # If i wasn't consistent with j:
                if self.domains[i].length == 0: # If domain is empty, return False - No more solutions possible to trial
                    return False
                for k in self.crossword.neighbors(i): 
                    if k != j:
                        queue.append((k,i)) # Enqueue k,i arc
        
        return True # Once queue empty, arc-consistency should have been enforced.

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
    
        for var in copy.deepcopy(assignment):
            if not assignment[var]: # If no value assigned, return False
                return False

        for variable in copy.deepcopy(self.crossword.variables):
            if variable not in assignment: # If any variable not in 'assignment'
                return False

        return True 

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for index1, var in enumerate(copy.deepcopy(assignment)): # Loop over assignment vars
            for index2, var_check in enumerate(copy.deepcopy(assignment)):
                if index1 == index2:
                    continue
                # All vars must be distinct
                if assignment[var] == assignment[var_check]:
                    return False         
            # All vars are correct length
            if len(assignment[var]) != var.length:
                return False
            # No conflicts between neighbors
            neighbors = self.crossword.neighbors(assignment[var])
            for neighbor in neighbors:
                i,j = self.crossword.overlaps[var,neighbor] # Get overlap co-ords
                if assignment[var][i] != self.domains[neighbor][j]:
                    return False
        return True # If consistent

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        neighbors = self.crossword.neighbors(var) # Get var's neighbors
        unassigned = [neighbor for neighbor in neighbors if neighbor not in assignment] # check for unnassigned variables in var's neighbors
        rankings = dict() # Initialise a dictionary to count how many potential neighbor words are ruled out when selecting each word in var's domain.

        for neighbor in unassigned: # Loop over unasssigned neighbors
            i,j = self.crossword.overlaps[var, neighbor] # Get index of overlapping indices
            n = 0 # Initialise count of eliminated choices
            for var_word in var:
                for neighbor_word in self.crossword.domains[neighbor]: # Loop over words in neighbors' domain
                    if var_word[i] != neighbor_word[j]:
                        n += 1 # Increase count by one, as arc inconsistency
                rankings[var_word] = rankings.get(var_word, 0) + n # Add count to 'rankings' dictionary
        
        # Having iterated over all neighbors, re-order dictionary in ascending order of n
        ordered_variabes = [item[0] for item in sorted(rankings.items(), key=lambda item: item[1])]
        return ordered_variabes

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned = [node for node in copy.deepcopy(self.crossword.variables) if node not in assignment]
        # Count number of strings in node's domain
        domainCounts = dict()
        for node in unassigned:
            domainCounts[node] = len(self.domains[node]) # Add to dict the length of domain for each variable
        domainCounts = dict(item for item in sorted(domainCounts.items(), key=lambda item: item[1])) # Order dictionary by count of remaining values in domain
        # Pick lowest. If TIE, choose variable w most neighbors.
        minDomains = dict()
        minCount = min(domainCounts.values()) # Get minimum count value
        domainCounts_copy = copy.deepcopy(domainCounts) # Create copy of dict
        for key, value in  domainCounts_copy.items():
            if value == minCount:
                minDomains[key] = value # Add all keys with smallest length domains

        if len(minDomains) == 1:
            return self.crossword.variables[minDomains.keys()[0]] # Return unnassigned variable
        else: # Order next by their no. neighbors
            neighborCount = dict() # Initialise dict for neighbor count
            for key, value in minDomains.items():
                count = len(self.crossword.neighbors(key))
                neighborCount[key] = count # Add key, count pair to dict

            minNeighborCount = min(neighborCount.values()) # Get min no. neighbors
            minNeighbors = dict() # Initialise dictionary for storing the neighbor counts
            for var, neighbors in copy.deepcopy(neighborCount):
                if neighbors == minNeighborCount: # All var's w min no. neighbors added to new dict
                    minNeighbors[var] = neighbors
             
            if len(minNeighbors) == 1:
                return self.crossword.variables[minNeighbors.keys()[0]]
            else: # Pick any with min no. neighbors
                choice = random.choice(minNeighbors.keys())
                return self.crossword.variables[choice]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Check if assignment complete
        checkCompletion = assignment_complete(assignment)
        if checkCompletion:
            return assignment # return complete assignment
        else:
            var = select_unassigned_variable(assignment) # select unassigned var
            for value in copy.deepcopy(self.domains[var]) # loop through domain values
                test_assignment = copy.deepcopy(assignment)
                test_assignment[var] = value # trial adding each value to the assignment
                checkConsistency = consistent(test_assignment) # check if assignment nodes are consistent w new value
                if checkConsistency: # If consistent...
                    assignment[var] = value # update actual 'assignment'
                    result = backtrack(assignment) # recursion - call backtrack on new 'assignment'!
                    if result: # If result returns array, must be complete
                        return result
                    assignment.remove(var) # If completion impossible, backtrack to try new value in domain

        # If not possible to complete w current assignment of values, return None & backtrack
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()

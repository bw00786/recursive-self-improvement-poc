# LangGraph

LangGraph models agent workflows as a state graph: nodes are functions that
receive and return state, and edges define execution order. Conditional edges
route execution based on the current state, which enables loops such as
retry-until-pass.

The state is a typed dictionary that every node reads and partially updates.
StateGraph is compiled into a runnable application with compile(); START and
END mark the entry and exit points of the graph.

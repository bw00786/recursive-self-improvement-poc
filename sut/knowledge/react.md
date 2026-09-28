# React

React builds user interfaces from components. The virtual DOM is an in-memory
representation of the UI; React diffs the new virtual DOM against the previous
one in a process called reconciliation and applies the minimal set of changes
to the real DOM.

Hooks add state and lifecycle features to function components: useState holds
local state, useEffect runs side effects after render, and useMemo caches an
expensive computation until its dependencies change.

Keys on list items help reconciliation match elements across renders; unstable
keys such as array indexes cause unnecessary re-renders and state bugs.

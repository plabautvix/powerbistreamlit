// The `Streamlit` object exists because our html file includes
// `streamlit-component-lib.js`.
// If you get an error about "Streamlit" not being defined, that
// means you're missing that file.

function sendValue(value) {
  Streamlit.setComponentValue(value);
}

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
function onRender(event) {
  // Only run the render code the first time the component is loaded.
  if (!window.rendered) {
    const gridContainer = document.getElementById('gridContainer');
    const selectedInfo = document.getElementById('selectedInfo');

    let selectedPositions = [];
    const restrictedPositions = event.detail.args.positions || []; // Receives the list from Python

    function generateStaticGrid() {
      const rows = 7; // Adjust to fit the range of rows in your list
      const cols = 3;

      for (let row = 1; row <= rows; row++) {
        for (let col = 1; col <= cols; col++) {
          const cellPosition = `ROW${row}, COL${col}`;
          const isRestricted = restrictedPositions.includes(`:red[${cellPosition}]`);

          const cell = document.createElement('div');
          cell.className = 'cell';
          cell.textContent = cellPosition;
          cell.dataset.row = row;
          cell.dataset.col = col;

          // Highlight restricted positions in red
          if (isRestricted) {
            cell.classList.add('restricted');
            cell.style.backgroundColor = "#ff6666"; // Red color
            cell.style.color = "white"; // White text for contrast
          }

          // Add click event for all cells
          cell.addEventListener('click', () => {
            const position = cellPosition;

            if (isRestricted) {
              // Alert if trying to select a restricted cell
              alert(`The position ${position} is occupied and cannot be selected.`);
              return;
            }

            // Check if a different row is selected
            if (
              selectedPositions.length > 0 &&
              !selectedPositions[0].startsWith(`ROW${row}`)
            ) {
              alert('You can only select cells from the same row!');
              return;
            }

            // Toggle selection
            if (cell.classList.contains('selected')) {
              cell.classList.remove('selected');
              selectedPositions = selectedPositions.filter(pos => pos !== position);
            } else {
              cell.classList.add('selected');
              selectedPositions.push(position);
            }

            // Update the display and send data to Streamlit
            selectedInfo.textContent = `Selected Positions: ${selectedPositions.join(' | ')}`;
            sendValue(selectedPositions); // Send to Streamlit
          });

          gridContainer.appendChild(cell);
        }
      }
    }

    generateStaticGrid();
    Streamlit.setComponentReady();
    window.rendered = true;
  }
}

// Render the component whenever python send a "render event"
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
// Tell Streamlit that the component is ready to receive events
Streamlit.setComponentReady();
// Render with the correct height, if this is a fixed-height component
Streamlit.setFrameHeight(430);

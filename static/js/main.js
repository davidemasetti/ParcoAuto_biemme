document.addEventListener('DOMContentLoaded', function() {
    const carGrid = document.getElementById('carGrid');
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const importButton = document.getElementById('importXML');

    function loadCars(search = '') {
        fetch(`/api/cars/?search=${encodeURIComponent(search)}`)
            .then(response => response.json())
            .then(cars => {
                carGrid.innerHTML = '';
                cars.forEach(car => {
                    const card = document.createElement('div');
                    card.className = 'col-md-4 mb-4';
                    card.innerHTML = `
                        <div class="card h-100">
                            <img src="${car.image}" class="card-img-top" alt="${car.title}">
                            <div class="card-body">
                                <h5 class="card-title">${car.title}</h5>
                                <p class="card-text">
                                    <strong>Price:</strong> €${car.price.toLocaleString()}<br>
                                    <strong>Year:</strong> ${car.year}<br>
                                    <strong>KM:</strong> ${car.km.toLocaleString()}<br>
                                    <strong>Fuel:</strong> ${car.fuel_type}
                                </p>
                                <a href="/car/${car.id}" class="btn btn-primary">View Details</a>
                            </div>
                        </div>
                    `;
                    carGrid.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error loading cars:', error);
                alert('Error loading cars. Please try again later.');
            });
    }

    if (searchButton) {
        searchButton.addEventListener('click', () => {
            loadCars(searchInput.value);
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadCars(searchInput.value);
            }
        });
    }

    if (importButton) {
        importButton.addEventListener('click', () => {
            importButton.disabled = true;
            fetch('/api/import-xml/', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    loadCars();
                })
                .catch(error => {
                    console.error('Error importing XML:', error);
                    alert('Error importing XML. Please try again later.');
                })
                .finally(() => {
                    importButton.disabled = false;
                });
        });
    }

    // Initial load
    if (carGrid) {
        loadCars();
    }
});

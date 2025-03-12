document.addEventListener('DOMContentLoaded', function() {
    const carGrid = document.getElementById('carGrid');
    const filterForm = document.getElementById('filterForm');
    const importButton = document.getElementById('importXML');

    function loadCars(filters = {}) {
        // Costruisci i parametri della query
        const params = new URLSearchParams();

        // Aggiungi i filtri ai parametri
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== '') {
                params.append(key, value);
            }
        });

        // Mostra indicatore di caricamento
        carGrid.innerHTML = '<div class="col-12 text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Caricamento...</span></div></div>';

        fetch(`/api/cars/?${params.toString()}`)
            .then(response => response.json())
            .then(cars => {
                carGrid.innerHTML = '';
                if (cars.length === 0) {
                    carGrid.innerHTML = '<div class="col-12"><div class="alert alert-info">Nessuna auto trovata con i filtri selezionati.</div></div>';
                    return;
                }
                cars.forEach(car => {
                    const card = document.createElement('div');
                    card.className = 'col-md-4 mb-4';
                    card.innerHTML = `
                        <div class="card h-100">
                            <img src="${car.image}" class="card-img-top" alt="${car.title}" onerror="this.src='/static/img/no-image.svg'">
                            <div class="card-body">
                                <h5 class="card-title">${car.title}</h5>
                                <p class="card-text">
                                    <strong>Prezzo:</strong> €${car.price.toLocaleString()}<br>
                                    <strong>Anno:</strong> ${car.year}<br>
                                    <strong>KM:</strong> ${car.km.toLocaleString()}<br>
                                    <strong>Carburante:</strong> ${car.fuel_type}
                                </p>
                                <a href="/car/${car.id}" class="btn btn-primary">Dettagli</a>
                            </div>
                        </div>
                    `;
                    carGrid.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error loading cars:', error);
                carGrid.innerHTML = '<div class="col-12"><div class="alert alert-danger">Errore nel caricamento delle auto. Riprova più tardi.</div></div>';
            });
    }

    filterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const filters = {
            min_price: document.getElementById('minPrice').value,
            max_price: document.getElementById('maxPrice').value,
            min_year: document.getElementById('minYear').value,
            max_year: document.getElementById('maxYear').value,
            min_km: document.getElementById('minKm').value,
            max_km: document.getElementById('maxKm').value,
            fuel_type: document.getElementById('fuelType').value,
            transmission: document.getElementById('transmission').value,
            body_type: document.getElementById('bodyType').value,
            color: document.getElementById('color').value
        };
        loadCars(filters);
    });

    filterForm.addEventListener('reset', (e) => {
        setTimeout(() => loadCars(), 0);
    });

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
                    alert('Errore nell\'importazione XML. Riprova più tardi.');
                })
                .finally(() => {
                    importButton.disabled = false;
                });
        });
    }

    // Caricamento iniziale
    loadCars();
});
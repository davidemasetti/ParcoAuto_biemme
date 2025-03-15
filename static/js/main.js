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
        carGrid.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Caricamento...</span></div></div>';

        fetch(`/api/cars/?${params.toString()}`)
            .then(response => response.json())
            .then(cars => {
                carGrid.innerHTML = '';
                if (cars.length === 0) {
                    carGrid.innerHTML = '<div class="alert alert-info">Nessuna auto trovata con i filtri selezionati.</div>';
                    return;
                }
                cars.forEach(car => {
                    const card = document.createElement('div');
                    card.className = 'car-card mb-4';
                    card.innerHTML = `
                        <div class="card">
                            <div class="row g-0">
                                <div class="col-md-4">
                                    <img src="${car.image}" class="img-fluid rounded-start car-image" 
                                         alt="${car.title}" onerror="this.src='/static/img/no-image.svg'">
                                </div>
                                <div class="col-md-8">
                                    <div class="card-body">
                                        <h4 class="card-title">${car.title}</h4>
                                        <div class="d-flex justify-content-between align-items-center mb-3">
                                            <h3 class="text-primary mb-0">€ ${car.price.toLocaleString()}</h3>
                                            <a href="/car/${car.id}" class="btn btn-primary">
                                                <i class="fas fa-info-circle"></i> Dettagli
                                            </a>
                                        </div>
                                        <div class="row">
                                            <div class="col-sm-6">
                                                <p class="mb-1">
                                                    <i class="fas fa-calendar"></i> Anno: ${car.year}
                                                </p>
                                                <p class="mb-1">
                                                    <i class="fas fa-road"></i> Km: ${car.km.toLocaleString()}
                                                </p>
                                            </div>
                                            <div class="col-sm-6">
                                                <p class="mb-1">
                                                    <i class="fas fa-gas-pump"></i> ${car.fuel_type}
                                                </p>
                                                <p class="mb-1">
                                                    <i class="fas fa-cog"></i> ${car.transmission}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    carGrid.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error loading cars:', error);
                carGrid.innerHTML = '<div class="alert alert-danger">Errore nel caricamento delle auto. Riprova più tardi.</div>';
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
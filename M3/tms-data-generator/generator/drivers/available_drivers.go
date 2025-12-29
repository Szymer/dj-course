package drivers

import (
	"fmt"
	"strings"
	"time"
)

// AvailableDriver reprezentuje dostępność kierowcy w danym dniu.
// Status: "available" - kierowca dostępny, "day off" - dzień wolny.
type AvailableDriver struct {
    ID            int
    DriverID      int
    AvailableDate time.Time
    Status        string // "available", "day off"
}

// GenerateAvailableDrivers generuje dostępność kierowców na określoną liczbę dni.
// Co 7. dzień ustawia status "day off".
func GenerateAvailableDrivers(drivers []Driver, days int) []AvailableDriver {
	var result []AvailableDriver
	id := 1
	for _, d := range drivers {
		for i := 0; i < days; i++ {
			date := time.Now().AddDate(0, 0, i)
			status := "available"
			// Przykładowa losowa logika na "day off"
			if i%7 == 6 { // co 7 dzień wolny
				status = "day off"
			}
			result = append(result, AvailableDriver{
				ID:            id,
				DriverID:      d.ID,
				AvailableDate: date,
				Status:        status,
			})
			id++
		}
	}
	return result
}

// GenerateAvailableDriversInsertStatements generuje polecenia INSERT dla dostępności kierowców.
// Używa pola status typu string.
func GenerateAvailableDriversInsertStatements(avail []AvailableDriver) string {
	var sb strings.Builder
	for _, a := range avail {
		sb.WriteString(fmt.Sprintf(
			"INSERT INTO available_drivers (id, driver_id, available_date, status) VALUES (%d, %d, '%s', '%s');\n",
			a.ID, a.DriverID, a.AvailableDate.Format("2006-01-02"), a.Status))
	}
	return sb.String()
}

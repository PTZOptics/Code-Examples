using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;

/// <summary>
/// This program demonstrates how to make an HTTP API call to a PTZOptics camera
/// to recall a preset position using Digest Authentication.
/// It prompts the user for connection details and sends a GET request
/// to the camera's CGI endpoint to trigger the preset recall.
/// </summary>
class Program
{
    static async Task Main(string[] args)
    {
        // 1. Get User Input -> IP Address, Username, Password, Preset Number
        Console.Write("Enter IP Address (e.g., 192.168.1.50): ");
        string ipAddress = Console.ReadLine()?.Trim();

        Console.Write("Enter Username: ");
        string username = Console.ReadLine()?.Trim();

        Console.Write("Enter Password: ");
        string password = Console.ReadLine()?.Trim();

        Console.Write("Enter Preset Number: ");
        string presetNumber = Console.ReadLine()?.Trim();

        // 2. Construct the URL based on your specific format
        string url = $"http://{ipAddress}/cgi-bin/ptzctrl.cgi?ptzcmd&poscall&{presetNumber}";

        Console.WriteLine($"\nTargeting: {url}");
        Console.WriteLine("Sending request...");

        // 3. Configure the Handler for Digest Authentication
        // HttpClientHandler will automatically handle the 401 Challenge/Response handshake required for Digest.
        var handler = new HttpClientHandler
        {
            Credentials = new NetworkCredential(username, password)
        };

        // 4. Create the Client and Send Request
        using (var client = new HttpClient(handler))
        {
            try
            {
                // Send the GET request
                HttpResponseMessage response = await client.GetAsync(url);

                // 5. Output Results
                if (response.IsSuccessStatusCode)
                {
                    Console.WriteLine("Success! Command sent.");
                    Console.WriteLine($"Status Code: {response.StatusCode}");

                    string content = await response.Content.ReadAsStringAsync();
                    if (!string.IsNullOrWhiteSpace(content))
                    {
                        Console.WriteLine($"Response: {content}");
                    }
                }
                else
                {
                    Console.WriteLine($"Error: The camera returned status code {response.StatusCode}");
                    Console.WriteLine($"Reason: {response.ReasonPhrase}");
                }
            }
            catch (HttpRequestException e)
            {
                Console.WriteLine($"\nNetwork Error: {e.Message}");
            }
            catch (Exception e)
            {
                Console.WriteLine($"\nAn unexpected error occurred: {e.Message}");
            }
        }

        Console.WriteLine("\nPress Enter to exit...");
        Console.ReadLine();
    }
}

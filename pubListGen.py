import requests
from bs4 import BeautifulSoup

# Function to fetch and parse publications from a given URL
def fetch_publications(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    publications = []
    for item in soup.find_all('div', class_='result_item'):
        pub = {}

        title_tag = item.find('h3')
        if title_tag:
            pub['title'] = title_tag.text.strip()

        authors_tag = item.find('div', class_='authors')
        if authors_tag:
            pub['authors'] = authors_tag.text.strip()

        doi_tag = item.find('a', class_='doi_link')
        if doi_tag:
            pub['doi'] = doi_tag.text.strip()

        journal_tag = item.find('span', class_='citation')
        if journal_tag:
            journal_info = journal_tag.text.strip().split('.')
            if len(journal_info) >= 2:
                pub['journal'] = journal_info[0].strip()
                pub['year'] = journal_info[1].strip()[:4]
            else:
                pub['journal'] = 'No Journal'
                pub['year'] = 'No Year'
        else:
            pub['journal'] = 'No Journal'
            pub['year'] = 'No Year'

        publications.append(pub)
    
    return publications

# Base URL
base_url = 'https://library.med.nyu.edu/api/publications/?person=rizzoj01&sort=display_rank&in-biosketch=yes&offset={}'

# List to hold all publications
all_publications = []

# Loop over multiple offsets (assuming 10 results per page)
for offset in range(0, 50, 10):  # Adjust the range as needed
    url = base_url.format(offset)
    print(url)
    fetch_publications(url)
    all_publications.extend(fetch_publications(url))
    
# Generate the static HTML content with your website's structure
html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <meta name="description" content="List of publications from Rizzo Lab" />
    <meta name="author" content="Junchi Feng" />
    <title>Publications - Rizzo Lab</title>
    <link rel="icon" type="image/x-icon" href="assets/favicon.ico" />
    <script src="https://use.fontawesome.com/releases/v6.3.0/js/all.js" crossorigin="anonymous"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/simple-line-icons/2.5.5/css/simple-line-icons.min.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,700,300italic,400italic,700italic" rel="stylesheet" type="text/css" />
    <link href="css/styles.css" rel="stylesheet" />
</head>
<body id="page-top">
    <a class="menu-toggle rounded" href="#"><i class="fas fa-bars"></i></a>
    <nav id="sidebar-wrapper">
        <ul class="sidebar-nav">
            <li class="sidebar-brand"><a href="index.html">Rizzo Lab</a></li>
            <li class="sidebar-nav-item"><a href="index.html">About</a></li>
            <li class="sidebar-nav-item"><a href="team.html">The Team</a></li>
            <li class="sidebar-nav-item"><a href="index.html">Projects</a></li>
            <li class="sidebar-nav-item"><a href="#publications">Publications</a></li>
        </ul>
    </nav>


    <section class="content-section" id="publications">
        <div class="container px-4 px-lg-5">
            <div class="content-section-heading text-center">
                <h2 class="text-secondary mb-0">Publications</h2>
            </div>
            <div class="row">
                <div class="col-lg-12 mx-auto">
'''

# Insert publication data
for pub in all_publications:
    html_content += f'''
                    <div class="publication mb-4">
                        <h6>{pub.get('title', 'No Title')}</h6>
                        <p><strong>Authors:</strong> {pub.get('authors', 'No Authors')}</p>
                        <p><strong>Journal:</strong> {pub.get('journal', 'No Journal')}</p>
                        <p> <strong>Year:</strong>({pub.get('year', 'No Year')})</p>
                        <p><strong>DOI:</strong> <a href="{pub.get('doi', '#')}" target="_blank">{pub.get('doi', 'No DOI')}</a></p>
                    </div>
    '''

# Close HTML content
html_content += '''
                </div>
            </div>
        </div>
    </section>

        <!-- Call to Action-->
        <section class="content-section bg-primary text-white">
            <div class="container px-4 px-lg-5 text-center">
                <h2 class="mb-4">Contact Us</h2>
                  <div class="container">
                    <div class="row text-center">
                      <!-- Location Section -->
                      <div class="col-md-4 mb-3 mb-md-0">
                        <h5>Location</h5>
                          <p> NYU Langone Ambulatory Care Center </p>
                          <p> Rusk Rehabilitation </p>
                        <p>240 E 38th St, 17th Floor,<br>New York, NY 10016</p>
                      </div>
                      <!-- Hours Section -->
                      <div class="col-md-4 mb-3 mb-md-0">
                        <h5>Lab Manager</h5>
                        <p>Mahya Beheshti<br>beheshti.mahya@gmail.com</p>
                      </div>
                      <!-- Contact Section -->
                      <div class="col-md-4">
                     
                        <h5>Lab Director</h5>
                          <p>John Ross Rizzo</p>
                          <p>JohnRoss.Rizzo@nyulangone.org</p>
          
                      </div>
                    </div>
                  </div>
            </div>
            
            
        </section>
        <!-- Map-->
        <div class="map" id="contact">
            <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3022.6694322419553!2d-73.97751272340075!3d40.74729883545296!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c259044548381f%3A0xbf1796b0c21aefd1!2s240%20E%2038th%20St%2017th%20Floor%2C%20New%20York%2C%20NY%2010016!5e0!3m2!1sen!2sus!4v1724552458473!5m2!1sen!2sus" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>

        </div>
        <!-- Footer-->
        <footer class="footer text-center">
            <div class="container px-4 px-lg-5">
                <ul class="list-inline mb-5">
                    <li class="list-inline-item">
                        <a class="social-link rounded-circle text-white mr-3" href="https://www.linkedin.com/in/jr-rizzo-3b447125/"><i class="icon-social-linkedin"></i></a>
                    </li>
                    <li class="list-inline-item">
                        <a class="social-link rounded-circle text-white mr-3" href="https://x.com/jrrizzo00"><i class="icon-social-twitter"></i></a>
                    </li>
                    <li class="list-inline-item">
                        <a class="social-link rounded-circle text-white" href="https://github.com/rizzojr01"><i class="icon-social-github"></i></a>
                    </li>
                </ul>
                <p class="text-muted small mb-0">Copyright &copy; Rizzo Lab 2024</p>
            </div>
        </footer>
        <!-- Scroll to Top Button-->
        <a class="scroll-to-top rounded" href="#page-top"><i class="fas fa-angle-up"></i></a>
        <!-- Bootstrap core JS-->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
        <!-- Core theme JS-->
        <script src="js/scripts.js"></script>
    </body>
</html>
'''

# Write the HTML content to a file
with open('publications.html', 'w') as file:
    file.write(html_content)

print("Static HTML page 'publications.html' has been generated.")

